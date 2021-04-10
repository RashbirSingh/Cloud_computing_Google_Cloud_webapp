import os

from flask import Flask, render_template

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="static/s3810585assignment1task2-3b3152f785f7.json"

from google.cloud import bigquery

app = Flask(__name__)


@app.route('/one')
def one():
    resultlist = []
    client = bigquery.Client()
    query_job = client.query(
        """
        SELECT time_ref, SUM(sumValue) AS trade_value
        FROM
        (SELECT time_ref, account, SUM(value) AS sumValue
        FROM `s3810585assignment1task2.gsquarterlySeptember20.gsquarterlySeptember20`
        GROUP BY time_ref, account) 
        AS result1
        GROUP BY time_ref
        ORDER BY trade_value DESC 
        LIMIT 10"""
    )

    results = query_job.result()  # Waits for job to complete.

    for row in results:
        resultlist.append({"time_ref":row.time_ref,
                      "trade_value":row.trade_value})

    return render_template('resultone.html',
                           answer="Answer 1",
                           results=resultlist)


@app.route('/two')
def two():
    resultlist = []
    client = bigquery.Client()
    query_job = client.query(
        """
        SELECT country_label , product_type, sum(case when account = 'Imports' then sumValue else - sumValue end) AS trade_deficit_value, status
        FROM 
        (SELECT country_code, time_ref, product_type, account, status, SUM(value) AS sumValue
        FROM `s3810585assignment1task2.gsquarterlySeptember20.gsquarterlySeptember20`
        WHERE time_ref > 201400 AND time_ref < 201800 AND status = 'F' AND product_type = 'Goods'
        GROUP BY country_code, time_ref, account, product_type, status) 
        AS result2
        FULL JOIN `s3810585assignment1task2.country_classification.country_classification`
        ON `s3810585assignment1task2.country_classification.country_classification`.country_code = result2.country_code
        GROUP BY country_label, product_type, status
        ORDER BY trade_deficit_value DESC 
        LIMIT 50"""
    )

    results = query_job.result()  # Waits for job to complete.

    for row in results:
        resultlist.append({"country_label":row.country_label,
                              "product_type":row.product_type,
                              "trade_deficit_value": row.trade_deficit_value,
                              "status":row.status})

    return render_template('resulttwo.html',
                           answer="Answer 2",
                           results=resultlist)


@app.route('/three')
def three():
    resultlist = []
    client = bigquery.Client()
    query_job = client.query(
        """
        SELECT service_label, trade_surplus_value
        FROM `s3810585assignment1task2.services_classification.services_classification`
        ,
        (SELECT trade_surplus_value
        FROM(
        (SELECT time_ref, SUM(sumValue) AS trade_value, country_code, code
        FROM
        (SELECT time_ref, account, SUM(value) AS sumValue, country_code, code
        FROM `s3810585assignment1task2.gsquarterlySeptember20.gsquarterlySeptember20`
        GROUP BY time_ref, account, country_code, code) 
        AS result1
        GROUP BY time_ref, country_code, code
        ORDER BY trade_value DESC 
        LIMIT 10) AS finalresult1
        
        FULL JOIN 
        
        (SELECT code, time_ref, country_code , product_type, sum(case when account = 'Export' then sumValue else - sumValue end) AS trade_surplus_value, status
        FROM 
        (SELECT country_code, time_ref, product_type, account, status, SUM(value) AS sumValue, code
        FROM `s3810585assignment1task2.gsquarterlySeptember20.gsquarterlySeptember20`
        WHERE time_ref > 201400 AND time_ref < 201800 AND status = 'F' AND product_type = 'Goods'
        GROUP BY country_code, time_ref, account, product_type, status, code) 
        AS result2
        GROUP BY country_code, product_type, status, time_ref, code
        ORDER BY trade_surplus_value DESC 
        LIMIT 50) As finalresult2
        ON finalresult1.time_ref = finalresult2.time_ref AND finalresult1.country_code = finalresult2.country_code)
        )
        AS Result3
        ORDER BY trade_surplus_value DESC 
        LIMIT 30"""
    )

    results = query_job.result()  # Waits for job to complete.

    for row in results:
        resultlist.append({"service_label":row.service_label,
                      "trade_surplus_value":row.trade_surplus_value})

    return render_template('resultthree.html',
                           answer="Answer 3",
                           results=resultlist)

@app.route('/')
def root():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)