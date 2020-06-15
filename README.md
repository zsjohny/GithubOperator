# GithubOperator

##  Automatically follow github user accounts

1. First find a github account with more followers and get his id

    ![githubNickname.png](image/githubNickname.png)

2. Get personal access token

    ![followers.png](image/followers.png)

    ![PersonalAccessTokens.png](image/PersonalAccessTokens.png)

    ```
    Click generate new token
    ```
   
3. Update config.ini
    ```
    [default]
    email = github email
    user = github nickname
    password = github password
    accessToken = github accessToken
    sourceUser = Most followers someone nickname
    exceeded = True 
    totalPage = 2000
    exceeded = True # default. to solve limit of github
    baseUrl = https://github.com/
    apiUrl = https://api.github.com
    retryDetailFile = retry_detail_file.txt
    retryCount = 10 # If your network is not good, this parameter can be increased
    retryCount = 10
    randomUser = False
    startPage = 5
    group = 10
    ```

4. Clone and Run
    ```
    git clone  && cd GithubOperator && ./AutoAddFollower.py
    ```
   
5. Run fail job
    If you found put_retry_detail_file.txt and retry_detail_file.txt not 
    empty, you need `./AutoAddFollower.py` again.
    
    
6. User random user `Update config.ini`
    ```
    randomUser = False
    ```

