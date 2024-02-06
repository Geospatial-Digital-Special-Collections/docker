## GDSC - pki

contents:  
- server_cert.pem  
- client_cert.pem  
- client_key.pem  

all from ~/.kube/config on kmaster

`
$ cat ~/.kube/config | grep certificate-authority-data | awk '{print $2}' | base64 -d > server_cert.pem
$ cat ~/.kube/config | grep client-certificate-data | awk '{print $2}' | base64 -d > client_cert.pem
$ cat ~/.kube/config | grep client-key-data | awk '{print $2}' | base64 -d > server_key.pem
`
