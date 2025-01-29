import os
import qianfan
from qianfan.resources.console.iam import IAM

# Set security authentication AK/SK
# Replace the parameters in the example below, replace your_iam_ak with the Access Key for security authentication, and replace your_iam_sk with the Secret Key. For how to obtain them, please refer to https://cloud.baidu.com/doc/Reference/s/9jwvz2egb
os.environ["QIANFAN_ACCESS_KEY"] = "<your_iam_ak>"
os.environ["QIANFAN_SECRET_KEY"] = "<your_iam_sk>"

# Call the create_bearer_token interface to get the bearerToken
response = IAM.create_bearer_token(expire_in_seconds=25920000)

print(response.body)

# If you need to directly output the bearerToken value, use the following
print(response.body.get('token'))
