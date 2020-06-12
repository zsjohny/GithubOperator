# GithubOperator

# 自动添加following
1. 先找一个follower 比较多的github账号, 获取他的id
    ![githubNickname.png](image/githubNickname.png)

2. 获取个人access token

    ![PersonalAccessTokens.png](image/PersonalAccessTokens.png)

    ```
    Click generate new token
    ```
   
3. 更新配置文件 config.ini
    ```
    [default]
    email = github email
    user = github nickname
    password = github password
    accessToken = github accessToken
    sourceUser = Most followers someone nickname
    exceeded = True 
    baseUrl = https://github.com/
    apiUrl = https://api.github.com
    ```

4. 克隆
    ```
    git clone  && cd GithubOperator && ./AutoAddFollower.py
    ```
