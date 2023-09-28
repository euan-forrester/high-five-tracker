"type":"metric",
"properties": {
    "metrics": [
        [
            "AWS/Events",
            "FailedInvocations",
            "RuleName",
            "${rule_name}"
        ]
    ],
    "period":300,
    "stat":"Sum",
    "region":"${region}",
    "title":"EventBridge cron failed invocations"
}
