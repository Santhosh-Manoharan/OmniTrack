from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, tempfile, requests

def get_token():
    t=os.getenv("PAPERLESS_TOKEN","")
    if not t:
        try:
            with open("/run/secrets/paperless_token","r") as f:
                t=f.read().strip()
        except: pass
    return t

URL=os.getenv("PAPERLESS_URL","http://localhost:8000")+"/api/documents/post_document/"

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0))
        b=json.loads(self.rfile.read(n))
        t=str(b.get("title","Untitled"))
        c=str(b.get("content",""))
        tmp=tempfile.NamedTemporaryFile(mode="w",suffix=".txt",delete=False)
        tmp.write(c);tmp.close()
        try:
            tok=get_token()
            with open(tmp.name,"rb") as f:
                r=requests.post(URL,headers={"Authorization":"Token "+tok},files={"document":("doc.txt",f,"text/plain")},data={"title":t},timeout=30)
            result=r.json()
            doc_id=str(result.get("id",""))
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"id":doc_id}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error":str(e)}).encode())
        finally:
            os.unlink(tmp.name)
    def log_message(self,*a): pass

HTTPServer(("0.0.0.0",int(os.getenv("PORT","8888"))),H).serve_forever()
