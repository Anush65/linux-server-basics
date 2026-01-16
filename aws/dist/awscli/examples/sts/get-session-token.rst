**To get a set of short term credentials for an IAM identity**

The following ``get-session-token`` command retrieves a set of short-term credentials for the IAM identity making the call. The resulting credentials can be used for requests where multi-factor authentication (MFA) is required by policy. The credentials expire 15 minutes after they are generated. ::

    aws sts get-session-token \
        --duration-seconds 900 \
        --serial-number "YourMFADeviceSerialNumber" \
        --token-code 123456

Output::

    {
        "Credentials": {
            "AccessKeyId": "replace_with_your_AccessKeyId",
            "SecretAccessKey": "replace_with_your_SecretAccessKey",
            "SessionToken": "replace_with_your_SessionToken",
            "Expiration": "2020-05-19T18:06:10+00:00"
        }
    }

For more information, see `Requesting Temporary Security Credentials <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_request.html#api_getsessiontoken>`__ in the *AWS IAM User Guide*.