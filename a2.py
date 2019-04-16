'''
COMP9321 2019 Term 1 Assignment Two Code Template
Student Name: Rong Jiang
Student ID: z5151899
'''
import requests, json
import sqlite3
import  uuid
import datetime
from flask import Flask
from flask_restplus import Api, Resource, fields, reqparse

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

#class setDecoder(json.JSONDecoder):
#    def decode(self, obj):
#        return list(json.JSONDecoder.decode(self, obj))

def create_db(db_file):
    '''
    uase this function to create a db, don't change the name of this function.
    db_file: Your database's name.
    '''
    connection = sqlite3.connect(db_file, check_same_thread=False)
    connection.execute("""
    CREATE TABLE IF NOT EXISTS worldbank (
        collection_id TEXT,
        indicator TEXT,
        indicator_value TEXT,
        creation_time DATETIME,
        entries JSON
    )
    """)

    return connection

def select_db(connection,iid):
    cur = connection.cursor()
    cur.execute('''SELECT * FROM worldbank WHERE indicator = ?''',(iid,))
    row = cur.fetchall()
    if not row:
        return 0
    else:
        return row

def insert_db(connection,indicator_id):
    #check if exist in database
    check = select_db(connection,indicator_id)
    if check:
        return 200
    try:
        r = requests.get('http://api.worldbank.org/v2/countries/all/indicators/{}?date=2013:2018&format=json&per_page=100'.format(indicator_id))
        datas = r.json()[1]
    except:
        return 404

    l = []
    for data in datas:
        dic = {"country":data['country']['value'],"date": data['date'],"value" : data['value']}
        l.append(dic)
    #print(l)
    now = datetime.datetime.now()
    ID=str(uuid.uuid4()).replace('-','')
    connection.execute("""
    INSERT INTO worldbank (collection_id, indicator, indicator_value, creation_time,entries)
    VALUES (?, ?, ?, ?, ?)
    """, [ID,data['indicator']['id'],data['indicator']['value'],now.strftime("%Y-%m-%dT%H:%M:%SZ"),json.dumps(l,cls = SetEncoder)])
    connection.commit()
    return ID

def select_db_c(connection,cid):
    cur = connection.cursor()
    cur.execute('''SELECT * FROM worldbank WHERE collection_id = ?''',(cid,))
    row = cur.fetchall()
    if not row:
        return 0
    else:
        return row

def delete_db(connection,cid):
    check = select_db_c(connection,cid)
    if not check:
        return 0
    cur = connection.cursor()
    cur.execute('''DELETE FROM worldbank WHERE collection_id = ?''',(cid,))
    connection.commit()
    return cur.rowcount


app = Flask(__name__)
api = Api(app)

i_collection = api.model('indicator_id', {'indicator_id' : fields.String('The indicator.')})
c_collection = api.model('collection_id', {'collection_id' : fields.String('The collection.')})

conn = create_db('data.db')
insert_db(conn,'NY.GDP.MKTP.CD')

@api.route('/data')
class collection(Resource):

    def get(self):
        #s = '{'
        l = []
        d = {}
        for row in conn.execute('SELECT * FROM worldbank;'):
            d['location'] = '/data/'+row[0]
            d['collection_id'] = row[0]
            d['creation_time'] = row[3]
            d['indicator'] = row[1]
            l.append(d.copy())
        return l,200

    @api.expect(c_collection)
    def delete(self):
        new_collection = api.payload
        check = delete_db(conn,new_collection['collection_id'])
        if not check:
            return {"ERROR":"Collection not found"},404
        return {"message" :"Collection = "+new_collection['collection_id']+" is removed from the database!"},200


    @api.expect(i_collection)
    def post(self):
        new_collection = api.payload
        msg = insert_db(conn,new_collection['indicator_id'])
        if msg == 200:
            check = select_db(conn,new_collection['indicator_id'])
            iid = check[0][0]
            time = check[0][3]
            return {"location" : "/data/"+iid,
        "collection_id" : iid,
        "creation_time": time,
        "indicator" : new_collection['indicator_id']}, 200
        elif msg == 404:
          return{"ERROR":"Collection not found in worldbank"},404
        else:
            row = select_db(conn,new_collection['indicator_id'])
            time = row[0][3]
            return {"location" : "/data/"+msg,
        "collection_id" : msg,
        "creation_time": time,
        "indicator" : new_collection['indicator_id']}, 201


@api.route('/data1/<string:collection_id>')
class collection1(Resource):
    def get(self,collection_id):
        row = select_db_c(conn,collection_id)
        if not row:
            return {},404
        d = {}
        d['collection_id'] = row[0][0]
        d['indicator'] = row[0][1]
        d['indicator_value'] = row[0][2]
        d['creation_time'] = row[0][3]
        d['entries'] = json.loads(row[0][4])
        return d,200

@api.route('/data2/<string:collection_id>/<string:year>/<string:country>')
class collection2(Resource):
    def get(self,collection_id,year,country):
        row = select_db_c(conn,collection_id)
        if not row:
            return {"ERROR":"Collection not found!"},404
        #print(row[0][4])
        entries = json.loads(row[0][4])
        value = 0
        for r in entries:
            if r['date']==year and r['country']==country:
                #print(r['value'])
                if not r['value']:
                    #print('Value is null')
                    return {"ERROR":'Null value being found'},404
                value = r['value']
                break
        if not value:
            return {"ERROR":'Value not found'},404
        d = {}
        d['collection_id'] = collection_id
        d['indicator'] = row[0][1]
        d['country'] = country
        d['year'] = year
        d['value'] = value
        return d,200

parser = reqparse.RequestParser()
parser.add_argument('q',type =str)
@api.route('/data3/<string:collection_id>/<string:year>')
class collection3(Resource):

    @api.expect(parser)
    def get(self,collection_id,year):
        args = parser.parse_args()
        query = args.get("q")
        row = select_db_c(conn,collection_id)
        if not row:
            return {"ERROR":"Collection not found!"},404
        entries = json.loads(row[0][4])
        if query[0:3]=='top':
            entries[:]=[d for d in entries if d['date'] == year and d['value'] != None]
            entries = sorted(entries, key = lambda i: i['value'],reverse=True)
            try:
                num = int(query[3:])
            except:
                return {"ERROR":"Please input a number following the query"},404
        elif query[0:6] == 'bottom':
            entries[:]=[d for d in entries if d['date'] == year and d['value'] != None]
            entries = sorted(entries, key = lambda i: i['value'])
            try:
                num = int(query[6:])
            except:
                return {"ERROR":"Please input a number following the query"},404
        else:
            return {"ERROR":"Please input correct query"},404
        dict = {}
        l=[]
        if not entries:
            return {"ERROR":"Null values being found"},404
        for i in range(0,num):
            dict['country']=entries[i]['country']
            dict['date']=entries[i]['date']
            dict['value']=entries[i]['value']
            l.append(dict.copy())
        return l,200

if __name__ == '__main__':
    app.run(debug=True)
