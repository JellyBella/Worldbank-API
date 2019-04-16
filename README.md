# Worldbank API

1 - Import a collection from the data service
This operation can be considered as an on-demand 'import' operation. The service will download the JSON data for all countries respective to the year 2013 to 2018 and identified by the indicator id given by the user and process the content into an internal data format.

2 - Deleting a collection with the data service
This operation deletes an existing collection from the database. 

3 - Retrieve the list of available collections
This operation retrieves all available collections. 

4 - Retrieve a collection

This operation retrieves a collection by its ID . The response of this operation will show the imported content from world bank API for all 6 years. That is, the data model that you have designed is visible here inside a JSON entry's content part.

5 - Retrieve economic indicator value for given country and a year

6 - Retrieve top/bottom economic indicator values for a given year

The <query> is an optional parameter which can be either of following: 
top<N> : Return top N countries sorted by indicator value
bottom<N> : Return bottom N countries sorted by indicator value
where N can be an integer value between 1 and 100. For example, a request like " GET /<collections>/< id>/2015?q=top10 " should returns top 10 countries according to the collection_id.