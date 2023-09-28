"type":"metric",
"properties": {
    "metrics": [
        [
            "AWS/SQS",
            "ApproximateNumberOfMessagesVisible",
            "QueueName",
            "${queue_name}"
        ]
    ],
    "period":300,
    "stat":"Sum",
    "region":"${region}",
    "title":"Dead-letter queue num items"
}