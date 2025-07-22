def customer_clustering(data):

    """

    Cluster all Customers based on their Behavior.

    

    Attributes:



    k_scores_: array of shape (n,) where n is no. of k values

        - The silhouette score corresponding to each k value

        

    k_timers_: array of shape (n,) where n is no. of k values

        - The time taken to fit n KMeans model corresponding to each k value

        

    elbow_value_: integer

        - The optimal value of k

        

    elbow_score_: float

        - The silhouette score corresponding to the optimal value of k.

    """

    #print(data)

    #data = data.reset_index(drop=False)

    data.replace([np.inf, -np.inf], np.nan, inplace=True)



    # Select float and integer columns

    numeric_columns = data.select_dtypes(include=['float', 'integer']).columns



    # Extract float and integer columns into one variable

    numeric_data = data[numeric_columns]



    # Handle missing values

    imputer = SimpleImputer(strategy='mean')

    numeric_data = imputer.fit_transform(numeric_data)

    numeric_data = pd.DataFrame(numeric_data, columns=numeric_columns)



    # Select non-numeric columns

    non_numeric_columns = data.select_dtypes(exclude=['float', 'integer']).columns



    # Extract non-numeric columns into another variable

    non_numeric_data = data[non_numeric_columns]



    # Concatenate both variables

    data = pd.concat([numeric_data, non_numeric_data], axis=1)

    #print(data.columns.tolist())



    cl_dataset = data.drop(columns=['city',

                                    'state',

                                    'Country',

                                    'Last_Order_Date',

                                    'Last_Churn_Date',

                                    'Customer_Loyalty_Status',

                                    'Just_Churned',

                                    #'Consecutive_Months_No_Invoice',

                                    'Last_Month_Sales',

                                    'Last_3_Month_Sales',

                                    'Last_6_Month_Sales',

                                    'Last_Month_Invoices',

                                    'Last_3_Month_Invoices',

                                    'Last_6_Month_Invoices',

                                    'Invoices_by_Year',

                                    'last_year_sales',

                                    'Invoices_by_Year'])



    name = cl_dataset["cust_name"]





    cl_dataset = cl_dataset.drop(columns=['cust_name'])



    enc = OneHotEncoder(handle_unknown='ignore')



    columns_to_drop = ['SiteId', 'Category_Description', 'Segment', 'High_Risk', 'Low_Risk', 'New_Customer', 'Established_Customer']



    # enc = joblib.load('encoder.joblib')

    # data_df = pd.DataFrame(data=data, columns=col_names)

    # enc_df = pd.DataFrame(data=enc.transform(data).toarray(), columns=enc.get_feature_names(col_names), dtype=bool)

    # df = pd.concat([data_df, enc_df], axis=1)



    # This data is fitted so it may be saved later for use for the active customers. 

    Coatings_Fitted = enc.fit(cl_dataset[['SiteId', 'Category_Description', 'Segment', 'High_Risk', 'Low_Risk', 'New_Customer', 'Established_Customer']])



    feature_array = enc.fit_transform(cl_dataset[['SiteId', 'Category_Description', 'Segment', 'High_Risk', 'Low_Risk', 'New_Customer', 'Established_Customer']]).toarray()

 

    # Get the feature names with a prefix

    feature_labels = enc.get_feature_names(input_features=['SiteId', 'CategoryDescription', 'Segment', 'High_Risk', 'Low_Risk', 'New Customer', 'Established Customer'])



    features = pd.DataFrame(feature_array, columns=feature_labels)



    cl_dataset.drop(columns=columns_to_drop, inplace=True)



    cl_dataset = pd.concat([cl_dataset, features], axis=1)



    #cl_dataset = pd.get_dummies(cl_dataset)



    #print(cl_dataset)



    #Rejoin userid to dataset (column concatenation)



    #cl_dataset = cl_dataset.dropna()

    

    scaler = MinMaxScaler()

    scaleddata = pd.DataFrame(data = scaler.fit_transform(cl_dataset), columns = cl_dataset.columns.tolist())



    ct = len(list(scaleddata.columns))

    # Instantiate the clustering model and visualizer

    model = KElbowVisualizer(KMeans(), k=ct)



    model.fit(scaleddata)        # Fit the data to the visualizer

    #model.show()        # Finalize and render the figure



    kmeans = cluster.KMeans(n_clusters=model.elbow_value_,

                            init="k-means++",

                            max_iter=1000)

    kmeans = kmeans.fit(scaleddata)

    

    scaleddata = pd.DataFrame(data = scaler.inverse_transform(scaleddata), columns = cl_dataset.columns.tolist())

    #print(scaleddata)



    scaleddata['state']= data['state']

    scaleddata['Country']= data['Country']

    scaleddata['city']= data['city']

    scaleddata['Last_Churn_Date']= data['Last_Churn_Date']

    scaleddata['Last_Order_Date']= data['Last_Order_Date']

    scaleddata['Customer_Loyalty_Status']= data['Customer_Loyalty_Status']

    #scaleddata['Consecutive_Months_No_Invoice']= data['Consecutive_Months_No_Invoice']

    scaleddata['Last_Month_Sales']= data['Last_Month_Sales']

    scaleddata['Last_3_Month_Sales']= data['Last_3_Month_Sales']

    scaleddata['Last_6_Month_Sales']= data['Last_6_Month_Sales']

    scaleddata['Last_Month_Invoices']= data['Last_Month_Invoices']

    scaleddata['Last_3_Month_Invoices']= data['Last_3_Month_Invoices']

    scaleddata['Last_6_Month_Invoices']= data['Last_6_Month_Invoices']

    scaleddata['Invoices_by_Year']= data['Invoices_by_Year']

    scaleddata['last_year_sales']= data['last_year_sales']

    scaleddata['Invoices_by_Year']= data['Invoices_by_Year']

    scaleddata['Just_Churned']= data['Just_Churned']



    scaleddata['Cluster'] = kmeans.labels_



    scaleddata = scaleddata.merge(name, how='inner', right_index=True, left_index=True)

    

    #print(scaleddata.columns)



    polar = scaleddata.groupby('Cluster').mean().reset_index()

    polar = pd.melt(polar,id_vars=["Cluster"])

    

    features = scaleddata.columns.tolist()

    features = pd.DataFrame(features)

    print(features.columns)

    

    #features.reset_index()

    

    return scaleddata, polar, Coatings_Fitted



Snapshot, polar, Coatings_Fitted = customer_clustering(Snapshot)