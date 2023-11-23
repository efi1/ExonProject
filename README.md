
# Exon Assignment

This assignment includes an automation infrastructure (written in Pyhon) for assuring the quality of a search engine of an ecommerce company.
The automation infrastructure includes two clients;
- a client which responsible for all DB interactions (create tables, insert, delete, count) and any additional sqlite command to be ran.
- a major client which responsible for all processes and activities; insertion (two processes), ranking update process, search term api and more.
  * this client inherits all DB client's functionality and name spaces, which then are used for its own functionalities.
The flow of the main functions of the major client reflects the business logic, and it includes these functions:
- insert_products_job -> which includes the process of inserting products to the products table.
- insert_new_site_into_search_engine_api --> which includes the api together with the process which repsible for inserting websites into the DB
  tables (websites, website_products).
   - in this process, only if the keywords and the product of a website (both are given in the inputs) exist in the products table, it is inserted
     into the website table as well into a common table (for both products and websites).
  * all the common id-s from the common table (websites_products) are written together with another given input - seniority - into a file.
- update_ranking_job -> is responsible to update the search_engine_ranking table with the values of the website insertion data.
    - it reads the file, which is created in the former process (in the insert_new_site_into_search_engine_api)  and mentioned before.
    - it updates then the search_engine_ranking with the websites_products with its content.
    - it calculated the parameter_value for each insertion given input - keywords, seniority and references.
    - finally, for each website, which represented by the website_product_rel_id, there are 3 entries (for each of the above-mentioned inputs).
      each entry will have its calculated value.
    - these 3 records can be sumed up (parameter_values) and can be ranked in compare tp all other entries.
- get_search_term_options api - this api getting a search term as an input (a key or a list of keys) and returns 3 websites which correspond this
  term. meaning that they have this search term among their keywords.
  Also, the result includes the 3 highest ranked websites, meaning the ones which is their total parameter_values are the highest in compare to
  other websites. This results take into account also the prioritiy of each of the website's elements which took place in the calculation of the
  parameter_value (it refer to the references, keywords and seniority).
  
- Before running the test:
  - clone it from Github to your local environment.
  - Go to 'src' folder (cli) and run this setup process: python setup.py install
    * you should run it while residing in the 'src' folder.

- How to run the test?  
  - from cli: python -m pytest
    * you should run it while being in the 'src' folder.

- I have only written a single automation test, which reflect the entire flow that described above.
- I will add some more test soon.
- A test cases description will be added in a separate file by an email.


  
