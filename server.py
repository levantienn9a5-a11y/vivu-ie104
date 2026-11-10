"""ViVu - local educational intercity bus booking application. Python 3.10+."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import sys
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
import sqlite3, json, os, secrets, hashlib, hmac, re, csv, io, argparse
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse, parse_qs
ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('VIVU_DB',str(ROOT/'data'/'vivu.db')))
CITIES=['TP. Hồ Chí Minh','Đà Lạt','Nha Trang','Vũng Tàu','Cần Thơ','Đà Nẵng','Hà Nội','Huế','Phan Thiết','Quy Nhơn','Buôn Ma Thuột','Pleiku','Kon Tum','Đồng Hới','Vinh','Thanh Hóa','Ninh Bình','Hải Phòng','Hạ Long','Sa Pa','Hà Giang','Lạng Sơn','Châu Đốc','Rạch Giá','Cà Mau','Bạc Liêu']
CITIES=list(dict.fromkeys(CITIES))
SCHEDULE_DAYS=91
# Routes, prices and travel times are illustrative data for this student project.
ROUTES=[
 ('TP. Hồ Chí Minh','Đà Lạt',7,280000),('TP. Hồ Chí Minh','Nha Trang',8,320000),
 ('TP. Hồ Chí Minh','Vũng Tàu',3,160000),('TP. Hồ Chí Minh','Cần Thơ',4,180000),
 ('Đà Nẵng','Huế',3,180000),('Hà Nội','Đà Nẵng',14,550000),
 ('TP. Hồ Chí Minh','Phan Thiết',4,200000),('TP. Hồ Chí Minh','Quy Nhơn',12,420000),
 ('TP. Hồ Chí Minh','Buôn Ma Thuột',8,320000),('TP. Hồ Chí Minh','Pleiku',11,400000),
 ('TP. Hồ Chí Minh','Kon Tum',12,430000),('TP. Hồ Chí Minh','Châu Đốc',6,240000),
 ('TP. Hồ Chí Minh','Rạch Giá',6,250000),('TP. Hồ Chí Minh','Cà Mau',8,300000),
 ('TP. Hồ Chí Minh','Bạc Liêu',7,270000),('Cần Thơ','Cà Mau',4,160000),
 ('Cần Thơ','Rạch Giá',3,140000),('Cần Thơ','Châu Đốc',3,150000),
 ('Đà Lạt','Nha Trang',4,200000),('Đà Lạt','Đà Nẵng',13,480000),
 ('Nha Trang','Quy Nhơn',5,230000),('Nha Trang','Đà Nẵng',10,380000),
 ('Đà Nẵng','Quy Nhơn',6,280000),('Đà Nẵng','Pleiku',7,300000),
 ('Đà Nẵng','Đồng Hới',5,220000),('Huế','Đồng Hới',4,180000),
 ('Hà Nội','Huế',13,480000),('Hà Nội','Vinh',6,250000),
 ('Hà Nội','Thanh Hóa',4,180000),('Hà Nội','Ninh Bình',2,120000),
 ('Hà Nội','Hải Phòng',2,130000),('Hà Nội','Hạ Long',3,180000),
 ('Hà Nội','Sa Pa',6,280000),('Hà Nội','Hà Giang',7,300000),
 ('Hà Nội','Lạng Sơn',3,160000),('Hà Nội','Đồng Hới',9,350000),
 ('Hải Phòng','Hạ Long',2,120000),('Vinh','Đà Nẵng',9,350000),
 ('Buôn Ma Thuột','Nha Trang',4,190000),('Pleiku','Kon Tum',2,100000)]
DAILY_SCHEDULES=[
 ('00:30','Sao Việt Travel','Giường nằm 36 chỗ',20000),
 ('05:00','An Bình Travel','Giường nằm 36 chỗ',0),
 ('06:30','ViVu Express','Limousine 24 phòng',70000),
 ('08:00','ViVu Express','Limousine 24 phòng',90000),
 ('09:30','Miền Xanh','Giường nằm 36 chỗ',10000),
 ('11:00','Hành Trình Việt','Limousine 24 phòng',60000),
 ('12:30','Sao Việt Travel','Giường nằm 36 chỗ',10000),
 ('14:30','An Bình Travel','Giường nằm 36 chỗ',0),
 ('16:00','Miền Xanh','Limousine 24 phòng',80000),
 ('18:30','Hành Trình Việt','Giường nằm 36 chỗ',20000),
 ('20:00','Sao Việt Travel','Limousine 24 phòng',80000),
 ('22:00','ViVu Express','Limousine 24 phòng',70000)]
from contextlib import contextmanager
@contextmanager
def connect():
 c=sqlite3.connect(DB,timeout=20); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON')
 try:
  yield c
  c.commit()
 except BaseException:
  c.rollback()
  raise
 finally:
  c.close()
def password(p,s): return hashlib.pbkdf2_hmac('sha256',p.encode(),s.encode(),180000).hex()
def init():
 DB.parent.mkdir(parents=True,exist_ok=True)
 with connect() as c:
  c.executescript('''
  CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,phone TEXT DEFAULT '',salt TEXT NOT NULL,password TEXT NOT NULL,role TEXT DEFAULT 'customer');
  CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER REFERENCES users(id),expires TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS trips(id INTEGER PRIMARY KEY,origin TEXT,destination TEXT,departure TEXT,arrival TEXT,operator TEXT,bus_type TEXT,price INTEGER,capacity INTEGER,active INTEGER DEFAULT 1);
  CREATE TABLE IF NOT EXISTS bookings(id INTEGER PRIMARY KEY,code TEXT UNIQUE,user_id INTEGER REFERENCES users(id),name TEXT,phone TEXT,email TEXT,total INTEGER,status TEXT,payment TEXT,promo TEXT,created TEXT);
  CREATE TABLE IF NOT EXISTS legs(id INTEGER PRIMARY KEY,booking_id INTEGER REFERENCES bookings(id),trip_id INTEGER REFERENCES trips(id),pickup TEXT,dropoff TEXT);
  CREATE TABLE IF NOT EXISTS seats(trip_id INTEGER REFERENCES trips(id),seat TEXT,booking_id INTEGER REFERENCES bookings(id),PRIMARY KEY(trip_id,seat));
  CREATE TABLE IF NOT EXISTS leg_seats(leg_id INTEGER REFERENCES legs(id),seat TEXT,PRIMARY KEY(leg_id,seat));
  ''')
  for name,email,pw,role in [('Quản trị ViVu','admin@vivu.vn','Admin@123','admin'),('Khách trải nghiệm','khach@vivu.vn','Khach@123','customer')]:
   if not c.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone():
    salt=secrets.token_hex(16); c.execute('INSERT INTO users(name,email,phone,salt,password,role) VALUES(?,?,?,?,?,?)',(name,email,'0901234567',salt,password(pw,salt),role))
  # Migrate only the untouched demo account, never a customer's registered name.
  c.execute("UPDATE users SET name='Khách trải nghiệm' WHERE email='khach@vivu.vn' AND name='Nguyễn Quang Thuận'")
  c.execute('CREATE INDEX IF NOT EXISTS idx_trips_route_departure ON trips(origin,destination,departure)')
  c.execute('CREATE INDEX IF NOT EXISTS idx_trips_departure ON trips(departure)')
  c.execute('CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id)')
  c.execute('CREATE INDEX IF NOT EXISTS idx_legs_booking ON legs(booking_id)')
  c.execute('CREATE INDEX IF NOT EXISTS idx_seats_booking ON seats(booking_id)')
  start=datetime.now().date()
  existing={(t[0],t[1],t[2]) for t in c.execute('SELECT origin,destination,departure FROM trips WHERE departure>=?',(str(start),))}
  pending=[]
  for days in range(SCHEDULE_DAYS):
   day=start+timedelta(days=days)
   for origin,dest,hours,base in ROUTES:
    for a,b in [(origin,dest),(dest,origin)]:
     for clock,op,kind,extra in DAILY_SCHEDULES:
      departure=datetime.fromisoformat(str(day)+'T'+clock)
      dep=departure.isoformat(timespec='minutes')
      if (a,b,dep) not in existing:
       pending.append((a,b,dep,(departure+timedelta(hours=hours)).isoformat(timespec='minutes'),op,kind,base+extra,24 if '24' in kind else 36))
  c.executemany('INSERT INTO trips(origin,destination,departure,arrival,operator,bus_type,price,capacity) VALUES(?,?,?,?,?,?,?,?)',pending)

def tripdict(c,t):
 d=dict(t); d['occupied']=[x[0] for x in c.execute('SELECT seat FROM seats WHERE trip_id=?',(t['id'],))]; d['available']=t['capacity']-len(d['occupied']); return d
def details(c,b):
 d=dict(b); d['legs']=[]
 for l in c.execute('SELECT * FROM legs WHERE booking_id=?',(b['id'],)):
  row=dict(l); row['trip']=dict(c.execute('SELECT * FROM trips WHERE id=?',(l['trip_id'],)).fetchone()); row['seats']=[s[0] for s in c.execute('SELECT seat FROM leg_seats WHERE leg_id=?',(l['id'],))]; d['legs'].append(row)
 return d
class APIError(Exception):
 def __init__(self,msg,status=400): self.msg=msg; self.status=status
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT/'public'),**kw)
 def log_message(self,fmt,*args): pass
 def reply(self,data,status=200):
  payload=json.dumps(data,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Content-Length',str(len(payload))); self.end_headers(); self.wfile.write(payload)
 def user(self,c,required=True,admin=False):
  token=self.headers.get('Authorization','').removeprefix('Bearer ')
  u=c.execute('SELECT u.id,u.name,u.email,u.phone,u.role FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token=? AND s.expires>?',(token,datetime.now().isoformat())).fetchone()
  if required and not u: raise APIError('Vui lòng đăng nhập để tiếp tục.',401)
  if admin and (not u or u['role']!='admin'): raise APIError('Bạn không có quyền quản trị.',403)
  return dict(u) if u else None
 def do_GET(self):
  if not self.path.startswith('/api/'): return super().do_GET()
  self.api('GET')
 def do_POST(self): self.api('POST')
 def do_PATCH(self): self.api('PATCH')
 def api(self,method):
  try:
   url=urlparse(self.path); path=url.path; q={k:v[0] for k,v in parse_qs(url.query).items()}; data={}
   if method!='GET':
    n=int(self.headers.get('Content-Length','0'))
    if n>20000: raise APIError('Dữ liệu quá lớn.',413)
    data=json.loads(self.rfile.read(n) or '{}')
   with connect() as c:
    if path=='/api/meta': return self.reply({'cities':CITIES,'today':str(datetime.now().date()),'maxDate':str(datetime.now().date()+timedelta(days=SCHEDULE_DAYS-1)),'routePairs':len(ROUTES),'tripsPerRoute':len(DAILY_SCHEDULES),'tripsPerDay':len(ROUTES)*2*len(DAILY_SCHEDULES),'scheduleDays':SCHEDULE_DAYS})
    if path=='/api/me': return self.reply({'user':self.user(c,False)})
    if path in ['/api/login','/api/register'] and method=='POST':
     email=str(data.get('email','')).strip().lower(); pw=str(data.get('password',''))
     if path.endswith('register'):
      name=str(data.get('name','')).strip(); phone=str(data.get('phone','')).strip()
      if len(name)<2 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or len(pw)<8 or not re.fullmatch(r'0\d{9}',phone): raise APIError('Nhập họ tên, email hợp lệ, số điện thoại 10 số và mật khẩu từ 8 ký tự.')
      salt=secrets.token_hex(16)
      try: c.execute('INSERT INTO users(name,email,phone,salt,password) VALUES(?,?,?,?,?)',(name,email,phone,salt,password(pw,salt)))
      except sqlite3.IntegrityError: raise APIError('Email đã được đăng ký.')
     u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
     if not u or not hmac.compare_digest(u['password'],password(pw,u['salt'])): raise APIError('Email hoặc mật khẩu chưa đúng.',401)
     token=secrets.token_urlsafe(32); c.execute('INSERT INTO sessions VALUES(?,?,?)',(token,u['id'],(datetime.now()+timedelta(days=2)).isoformat())); return self.reply({'token':token,'user':{k:u[k] for k in ['id','name','email','phone','role']}})
    if path=='/api/logout' and method=='POST':
     c.execute('DELETE FROM sessions WHERE token=?',(self.headers.get('Authorization','').removeprefix('Bearer '),)); return self.reply({'ok':True})
    if path=='/api/profile' and method=='PATCH':
     u=self.user(c); name=str(data.get('name','')).strip(); phone=str(data.get('phone',''))
     if len(name)<2 or not re.fullmatch(r'0\d{9}',phone): raise APIError('Họ tên hoặc số điện thoại không hợp lệ.')
     c.execute('UPDATE users SET name=?,phone=? WHERE id=?',(name,phone,u['id'])); return self.reply({'ok':True})
    if path=='/api/trips' and method=='GET':
     rows=c.execute('SELECT * FROM trips WHERE active=1 AND origin=? AND destination=? AND departure>=? AND departure<? AND departure>? ORDER BY departure',(q.get('origin'),q.get('destination'),q.get('date','')+'T00:00',q.get('date','')+'T99:99',datetime.now().isoformat(timespec='minutes'))).fetchall(); return self.reply([tripdict(c,t) for t in rows])
    if re.fullmatch(r'/api/trips/\d+',path) and method=='GET':
     t=c.execute('SELECT * FROM trips WHERE id=?',(path.rsplit('/',1)[1],)).fetchone()
     if not t: raise APIError('Không tìm thấy chuyến xe.',404)
     return self.reply(tripdict(c,t))
    if path=='/api/bookings' and method=='GET':
     u=self.user(c); return self.reply([details(c,b) for b in c.execute('SELECT * FROM bookings WHERE user_id=? ORDER BY id DESC',(u['id'],))])
    if path=='/api/lookup' and method=='POST':
     b=c.execute('SELECT * FROM bookings WHERE code=? AND phone=?',(str(data.get('code','')).upper().strip(),data.get('phone'))).fetchone()
     if not b: raise APIError('Không tìm thấy vé khớp mã vé và số điện thoại.',404)
     result=details(c,b); result.pop('email',None); return self.reply(result)
    if path=='/api/bookings' and method=='POST':
     u=self.user(c); name=str(data.get('name','')).strip(); phone=str(data.get('phone','')); email=str(data.get('email','')).strip()
     if len(name)<2 or not re.fullmatch(r'0\d{9}',phone) or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email): raise APIError('Thông tin hành khách chưa hợp lệ.')
     legs=data.get('legs',[]); count=data.get('passengers'); payment=data.get('payment'); promo=str(data.get('promo','')).upper().strip()
     if payment not in ['cash','demo']: raise APIError('Phương thức thanh toán không hợp lệ.')
     if type(count)!=int or not 1<=count<=6 or not isinstance(legs,list) or len(legs) not in [1,2]: raise APIError('Số hành khách hoặc hành trình không hợp lệ.')
     if promo not in ['', 'VIVU10']: raise APIError('Mã ưu đãi không hợp lệ.')
     c.execute('BEGIN IMMEDIATE'); total=0; checked=[]
     for l in legs:
      t=c.execute('SELECT * FROM trips WHERE id=? AND active=1',(l.get('tripId'),)).fetchone(); ss=l.get('seats',[])
      if not t or t['departure']<=datetime.now().isoformat(timespec='minutes'): raise APIError('Chuyến xe không còn khả dụng.')
      if not isinstance(ss,list) or len(ss)!=count or len(set(ss))!=count: raise APIError('Vui lòng chọn đủ ghế cho mỗi chiều.')
      valid={f'{x}{i:02}' for x in ['A','B'] for i in range(1,t['capacity']//2+1)}
      if any(s not in valid for s in ss): raise APIError('Ghế không hợp lệ.')
      if any(c.execute('SELECT 1 FROM seats WHERE trip_id=? AND seat=?',(t['id'],s)).fetchone() for s in ss): raise APIError('Một ghế vừa được đặt. Vui lòng tải lại và chọn ghế khác.',409)
      pickup='Bến xe '+t['origin']; dropoff='Bến xe '+t['destination']
      if l.get('pickup') not in [pickup,'Văn phòng '+t['operator']]: raise APIError('Điểm đón không hợp lệ.')
      total+=t['price']*count; checked.append((t,ss,l['pickup'],dropoff))
     if len(checked)==2:
      a,b=checked[0][0],checked[1][0]
      if a['origin']!=b['destination'] or a['destination']!=b['origin'] or b['departure']<=a['arrival']: raise APIError('Chuyến về phải ngược tuyến và khởi hành sau khi chuyến đi đến nơi.')
     if promo: total-=min(int(total*.1),100000)
     code='VV'+secrets.token_hex(4).upper(); cur=c.execute('INSERT INTO bookings(code,user_id,name,phone,email,total,status,payment,promo,created) VALUES(?,?,?,?,?,?,?,?,?,?)',(code,u['id'],name,phone,email,total,'confirmed',payment,promo,datetime.now().isoformat(timespec='seconds'))); bid=cur.lastrowid
     for t,ss,pick,drop in checked:
      lid=c.execute('INSERT INTO legs(booking_id,trip_id,pickup,dropoff) VALUES(?,?,?,?)',(bid,t['id'],pick,drop)).lastrowid
      for s in ss: c.execute('INSERT INTO seats VALUES(?,?,?)',(t['id'],s,bid)); c.execute('INSERT INTO leg_seats VALUES(?,?)',(lid,s))
     return self.reply(details(c,c.execute('SELECT * FROM bookings WHERE id=?',(bid,)).fetchone()),201)
    if re.fullmatch(r'/api/bookings/\d+/cancel',path) and method=='POST':
     u=self.user(c); bid=int(path.split('/')[3]); c.execute('BEGIN IMMEDIATE'); b=c.execute('SELECT * FROM bookings WHERE id=?',(bid,)).fetchone()
     if not b or (b['user_id']!=u['id'] and u['role']!='admin'): raise APIError('Không tìm thấy vé.',404)
     if b['status']=='cancelled': raise APIError('Vé đã được hủy.')
     first=c.execute('SELECT min(t.departure) FROM trips t JOIN legs l ON t.id=l.trip_id WHERE l.booking_id=?',(bid,)).fetchone()[0]
     if datetime.fromisoformat(first)-datetime.now()<timedelta(hours=2): raise APIError('Chỉ có thể hủy trước giờ khởi hành ít nhất 2 giờ.')
     c.execute("UPDATE bookings SET status='cancelled' WHERE id=?",(bid,)); c.execute('DELETE FROM seats WHERE booking_id=?',(bid,)); return self.reply({'ok':True})
    if path.startswith('/api/admin/'):
     self.user(c,admin=True)
     if path=='/api/admin/dashboard':
      return self.reply({'bookings':[details(c,b) for b in c.execute('SELECT * FROM bookings ORDER BY id DESC')],'users':[dict(x) for x in c.execute('SELECT id,name,email,phone,role FROM users')],'trips':[tripdict(c,t) for t in c.execute('SELECT * FROM trips WHERE departure>=? AND departure<? ORDER BY departure',(q.get('date',str(datetime.now().date()+timedelta(days=1)))+'T00:00',q.get('date',str(datetime.now().date()+timedelta(days=1)))+'T99:99'))]})
     if path=='/api/admin/trips' and method=='POST':
      try:
       a,b=data['origin'],data['destination']; dep=datetime.fromisoformat(data['departure']); arr=datetime.fromisoformat(data['arrival']); price=int(data['price']); cap=int(data['capacity']); op=str(data['operator']).strip(); kind=str(data['bus_type']).strip()
       if a not in CITIES or b not in CITIES or a==b or dep<=datetime.now() or arr<=dep or not 10000<=price<=2000000 or cap not in [24,36] or not op or kind not in ['Limousine 24 phòng','Giường nằm 36 chỗ'] or (kind=='Limousine 24 phòng' and cap!=24) or (kind=='Giường nằm 36 chỗ' and cap!=36): raise ValueError()
      except (ValueError,KeyError,TypeError): raise APIError('Thông tin chuyến xe không hợp lệ.')
      c.execute('INSERT INTO trips(origin,destination,departure,arrival,operator,bus_type,price,capacity) VALUES(?,?,?,?,?,?,?,?)',(a,b,dep.isoformat(timespec='minutes'),arr.isoformat(timespec='minutes'),op,kind,price,cap)); return self.reply({'ok':True},201)
     if re.fullmatch(r'/api/admin/trips/\d+',path) and method=='PATCH':
      tid=int(path.rsplit('/',1)[1]); t=c.execute('SELECT * FROM trips WHERE id=?',(tid,)).fetchone()
      if not t: raise APIError('Không tìm thấy chuyến.',404)
      if c.execute('SELECT 1 FROM seats WHERE trip_id=?',(tid,)).fetchone(): raise APIError('Chuyến đã có khách đặt, không thể sửa hoặc ẩn.')
      try:
       price=int(data.get('price',t['price'])); active=int(data.get('active',t['active']))
       if not 10000<=price<=2000000 or active not in [0,1]: raise ValueError()
      except (ValueError,TypeError): raise APIError('Giá hoặc trạng thái không hợp lệ.')
      c.execute('UPDATE trips SET price=?,active=? WHERE id=?',(price,active,tid)); return self.reply({'ok':True})
    raise APIError('Không tìm thấy chức năng.',404)
  except APIError as e: self.reply({'error':e.msg},e.status)
  except (ValueError,TypeError,KeyError,json.JSONDecodeError): self.reply({'error':'Dữ liệu gửi lên không hợp lệ.'},400)
  except Exception as e:
   print(type(e).__name__,str(e)); self.reply({'error':'Không thể xử lý yêu cầu. Vui lòng thử lại.'},500)
if __name__=='__main__':
 parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8000); parser.add_argument('--open-browser',action='store_true'); args=parser.parse_args()
 init()
 try:
  server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
 except OSError as e:
  print(f'Khong mo duoc cong {args.port}: {e}. Thu lai voi --port 8001.',flush=True)
  raise SystemExit(1)
 url=f'http://localhost:{args.port}'
 print(f'ViVu đang chạy tại {url}',flush=True)
 if args.open_browser:
  import webbrowser
  try: webbrowser.open(url)
  except Exception: print(f'Hay tu mo trinh duyet va truy cap {url}',flush=True)
 try: server.serve_forever()
 except KeyboardInterrupt: pass
 finally: server.server_close()
