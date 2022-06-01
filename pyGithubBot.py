#imports 
from ensurepip import version
import typer #This library helps to take cli input
import csv
import json
import os
import git
from github import Github
import getpass

app = typer.Typer()

def send_pull(name, url, v, username, password, g, osys):
    x = url.split("/") #We are splitting the url to obtain the organisation name and repo name
    org_name = x[len(x)-2]
    repo_name = x[len(x)-1]
    remote = f"https://{username}:{password}@github.com/{username}/{repo_name}.git"   #We create a remote for commit and push
    
    f = open(name+'\package.json','r')
    vdict = json.load(f)
    vdict['version'] = v    #Here we convert the json to string and change the version

    f2 = open(name+'\package-lock.json','r')
    
    vvdict = json.load(f2)
    vvdict['version'] = v

    f.close()
    f2.close()

    file = open(name+'\package.json','w')
    file2 = open(name+'\package-lock.json','w')

    json.dump(vdict,file)    #Here we convert string to json again
    json.dump(vvdict,file2)
    file.close()
    file2.close()

    #Now we add the changed files to git
    repo = git.Repo(name)
    repo.git.add('package.json')
    repo.git.add('package-lock.json')
    repo.index.commit('Update '+ osys +' to version '+v)  #Committing our changes
    origin = repo.remote(name="origin")
    origin.push()

    #Here we will generate a pull request
    pr_no = '0'
    pr_url = 'https://github.com/'+org_name+'/'+repo_name+'/pull'+'/'+pr_no
    try:
        upstream_user = g.get_user(org_name)
        upstream_repo = upstream_user.get_repo(repo_name)
        upstream_pullrequest = upstream_repo.create_pull("Update os to new version", "Updated", 'main', 
            '{}:{}'.format(username, 'main'), True)
        pr_no = str(upstream_pullrequest.number())
        pr_url ='https://github.com/'+org_name+'/'+repo_name+'/pull'+'/'+pr_no
    except:
        print("Pull Request already created. Commits will be updated.")
    return pr_url


def git_clone(name, url, v, username, pwd, upg, osys):
    #Logging in to github with credentials
    g = Github(username, pwd)
    github_user = g.get_user()
    y = url.replace('https://github.com/','')
    x = url.split("/")
    repo_name = x[len(x)-1]
    repo = g.get_repo(y) 
    github_user.create_fork(repo)    #Forking the repo to own account to edit
    x = url.split("/")
    repo_name = x[len(x)-1]
    new_url = 'https://github.com/'+username+'/'+repo_name
    path = name+'/package.json'
    isFile = os.path.isfile(path) 
    if isFile == False:     #If file already not cloned in that location, we clone it
        git.Repo.clone_from(new_url, name)
    f = open(name+'\package.json','r')
    vdict = json.load(f)
    version = vdict['version']
    row = []
    row.append(name)
    row.append(url)
    row.append(version)
    if(version>=v):
        row.append("True")
    else:
        row.append("False")
        if upg == True :
            row.append(send_pull(name, url, v, username, pwd, g, osys))
    f.close()
    return row

def read_csv(inp, v, upg, osys):
    username = input("Enter github username: ")
    pwd = input("Enter password(github token): ")   #Password can be encrypted, for now for easy use, it is taken as string

    #We open input csv file to obtain the records
    file = open(inp)
    type(file)
    csvreader = csv.reader(file)
    header = []
    header = next(csvreader)
    rows = []
    for row in csvreader:
        rows.append(row)
    names=[]
    url=[]
    rrows = []
    for i in range(len(rows)):
        rrows.append(git_clone(rows[i][0],rows[i][1],v,username,pwd,upg, osys))
    
    file.close()
    header.append("Version")
    header.append("Version_Satisfied")
    if upg == True:   #This will be called when user puts update cmd
        header.append('update_pr')

    file_write = open('output.csv','w')   #This will be our output csv
    csvwriter = csv.writer(file_write) 
    csvwriter.writerow(header) 
    csvwriter.writerows(rrows)
    file_write.close()


def repo(inp):
    file = open(inp)
    type(file)
    csvreader = csv.reader(file)
    header = []
    header = next(csvreader)
    rows = []
    for row in csvreader:
        rows.append(row)
    print()
    for i in range(len(rows)):
        print(('%d. '+rows[i][0]) %(i+1))
        print("Github Url: "+rows[i][1])
        y = rows[i][1].replace('https://github.com/','')
        x = rows[i][1].split("/") #We are splitting the url to obtain the organisation name 
        org_name = x[len(x)-2]
        g = Github()
        # get the authenticated user
        user = g.get_user(org_name)
        repo = g.get_repo(y)
        print("Name: "+repo.name)
        print("Description: "+repo.description)
        print("Default Branch: "+repo.default_branch)
        print("Forks Count: %d"%repo.forks_count)
        print("Created at: ",repo.created_at)
        print("Is the Repository Private: ",repo.private)
        print()

@app.command()
def info(inp:str, osys: str, v:str):
    read_csv(inp, v, False, osys)

@app.command()
def update(inp: str, osys: str, v:str):
    read_csv(inp, v, True, osys)

@app.command()
def repodetails(inp: str, osys: str):
    repo(inp)

if __name__ == "__main__":
    app()