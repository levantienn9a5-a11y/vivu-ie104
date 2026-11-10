"""Integration checks on an isolated temporary database, no external dependencies."""
import unittest, subprocess, sys, os, tempfile, time, json, urllib.request, urllib.error, concurrent.futures, sqlite3, socket
from pathlib import Path
from datetime import datetime,timedelta
ROOT=Path(__file__).resolve().parent
class BookingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(); cls.db=Path(cls.tmp.name)/'test.db'
  sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close();cls.base=f'http://127.0.0.1:{port}/api'
  cls.log=open(ROOT/'docs'/'test-server.log','w',encoding='utf8')
  cls.proc=subprocess.Popen([sys.executable,'-X','utf8',str(ROOT/'server.py'),'--port',str(port)],env={**os.environ,'VIVU_DB':str(cls.db)},stdout=cls.log,stderr=subprocess.STDOUT)
  for _ in range(30):
   try: cls.request('/meta');break
   except Exception:time.sleep(.1)
  else:raise RuntimeError('Server failed to start')
  cls.customer=cls.request('/login','POST',{'email':'khach@vivu.vn','password':'Khach@123'})[1]['token'];cls.admin=cls.request('/login','POST',{'email':'admin@vivu.vn','password':'Admin@123'})[1]['token']
  cls.day=str(datetime.now().date()+timedelta(days=2));cls.nextday=str(datetime.now().date()+timedelta(days=3))
  from urllib.parse import urlencode
  cls.trips=cls.request('/trips?'+urlencode({'origin':'TP. Hồ Chí Minh','destination':'Đà Lạt','date':cls.day}))[1]
  cls.ret=cls.request('/trips?'+urlencode({'origin':'Đà Lạt','destination':'TP. Hồ Chí Minh','date':cls.nextday}))[1][0]
 @classmethod
 def tearDownClass(cls): cls.proc.terminate();cls.proc.wait(timeout=10);cls.log.close();cls.tmp.cleanup()
 @classmethod
 def request(cls,path,method='GET',data=None,token=''):
  req=urllib.request.Request(cls.base+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+token} if token else {})})
  try:
   with urllib.request.urlopen(req,timeout=2) as r:return r.status,json.load(r)
  except urllib.error.HTTPError as e:return e.code,json.load(e)
 def payload(self,seat='A01',trip=None):
  t=trip or self.trips[0];return {'name':'Khach Kiem Thu','phone':'0901111222','email':'test@example.com','passengers':1,'payment':'demo','promo':'','legs':[{'tripId':t['id'],'seats':[seat],'pickup':'Bến xe '+t['origin']}]}
 def book(self,p):return self.request('/bookings','POST',p,self.customer)
 def test_01_search_and_login(self):
  self.assertEqual(len(self.trips),12);self.assertEqual(self.request('/login','POST',{'email':'khach@vivu.vn','password':'wrong'})[0],401)
 def test_02_register_unique(self):
  p={'name':'Nguyen Test','phone':'0901111222','email':'new@example.com','password':'Secret123'}
  self.assertEqual(self.request('/register','POST',p)[0],200);self.assertEqual(self.request('/register','POST',p)[0],400)
 def test_03_unauthorized(self):self.assertEqual(self.request('/bookings','POST',self.payload())[0],401)
 def test_04_permissions(self):self.assertEqual(self.request('/admin/dashboard',token=self.customer)[0],403)
 def test_05_price_server_and_discount(self):
  p=self.payload();p['total']=1;p['promo']='VIVU10';status,b=self.book(p);self.assertEqual(status,201);self.assertEqual(b['total'],self.trips[0]['price']*.9);self.assertEqual(len(b['legs']),1)
 def test_06_seat_collision(self):self.assertEqual(self.book(self.payload())[0],409)
 def test_07_invalid_seat(self):self.assertEqual(self.book(self.payload('Z99'))[0],400)
 def test_08_seat_count(self):
  p=self.payload('A03');p['passengers']=2;self.assertEqual(self.book(p)[0],400)
 def test_09_invalid_contact(self):
  p=self.payload('A03');p['phone']='123';self.assertEqual(self.book(p)[0],400)
 def test_10_invalid_promo(self):
  p=self.payload('A03');p['promo']='FAKE';self.assertEqual(self.book(p)[0],400)
 def test_11_roundtrip(self):
  p=self.payload('A04');p['legs'].append({'tripId':self.ret['id'],'seats':['B04'],'pickup':'Bến xe '+self.ret['origin']});s,b=self.book(p);self.assertEqual(s,201);self.assertEqual(len(b['legs']),2);self.assertEqual(b['total'],self.trips[0]['price']+self.ret['price'])
 def test_12_wrong_return_rolls_back(self):
  p=self.payload('A05');p['legs'].append({'tripId':self.trips[1]['id'],'seats':['A05'],'pickup':'Bến xe '+self.trips[1]['origin']});self.assertEqual(self.book(p)[0],400);self.assertNotIn('A05',self.request('/trips/'+str(self.trips[0]['id']))[1]['occupied'])
 def test_13_lookup(self):
  s,b=self.book(self.payload('A06'));self.assertEqual(s,201);s,result=self.request('/lookup','POST',{'code':b['code'],'phone':'0901111222'});self.assertEqual(s,200);self.assertEqual(result['code'],b['code']);self.assertEqual(self.request('/lookup','POST',{'code':b['code'],'phone':'0900000000'})[0],404)
 def test_14_cancel_and_rebook(self):
  _,b=self.book(self.payload('A07'));self.assertEqual(self.request('/bookings/'+str(b['id'])+'/cancel','POST',{},self.customer)[0],200);self.assertEqual(self.book(self.payload('A07'))[0],201)
 def test_15_cancel_cutoff(self):
  _,b=self.book(self.payload('A08',self.trips[2]))
  c=sqlite3.connect(self.db);c.execute('UPDATE trips SET departure=? WHERE id=?',((datetime.now()+timedelta(minutes=30)).isoformat(timespec='minutes'),self.trips[2]['id']));c.commit();c.close()
  self.assertEqual(self.request('/bookings/'+str(b['id'])+'/cancel','POST',{},self.customer)[0],400)
  c=sqlite3.connect(self.db);c.execute('UPDATE trips SET departure=? WHERE id=?',(self.trips[2]['departure'],self.trips[2]['id']));c.commit();c.close()
 def test_16_concurrent_booking(self):
  with concurrent.futures.ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda _:self.book(self.payload('A09'))[0],range(2)))
  self.assertEqual(sorted(results),[201,409])
 def test_17_admin_add_edit_hide(self):
  p={'origin':'Hà Nội','destination':'Huế','departure':self.day+'T09:00','arrival':self.day+'T22:00','operator':'Test Bus','bus_type':'Giường nằm 36 chỗ','price':300000,'capacity':36}
  self.assertEqual(self.request('/admin/trips','POST',p,self.admin)[0],201)
  d=self.request('/admin/dashboard?date='+self.day,token=self.admin)[1];t=next(t for t in d['trips'] if t['operator']=='Test Bus')
  self.assertEqual(self.request('/admin/trips/'+str(t['id']),'PATCH',{'price':350000},self.admin)[0],200);self.assertEqual(self.request('/admin/trips/'+str(t['id']),'PATCH',{'active':0},self.admin)[0],200)
 def test_18_admin_protect_booked_trip(self):self.assertEqual(self.request('/admin/trips/'+str(self.trips[0]['id']),'PATCH',{'active':0},self.admin)[0],400)
 def test_19_ownership(self):
  token=self.request('/login','POST',{'email':'new@example.com','password':'Secret123'})[1]['token'];b=self.request('/bookings',token=self.customer)[1][0];self.assertEqual(self.request('/bookings/'+str(b['id'])+'/cancel','POST',{},token)[0],404)
 def test_20_profile_and_logout(self):
  token=self.request('/login','POST',{'email':'new@example.com','password':'Secret123'})[1]['token'];self.assertEqual(self.request('/profile','PATCH',{'name':'New Name','phone':'0909999888'},token)[0],200);self.request('/logout','POST',{},token);self.assertIsNone(self.request('/me',token=token)[1]['user'])

 def test_21_expanded_schedules(self):
  from urllib.parse import urlencode
  meta=self.request('/meta')[1]
  self.assertEqual(meta['routePairs'],40);self.assertEqual(meta['tripsPerRoute'],12);self.assertEqual(meta['scheduleDays'],91)
  self.assertGreaterEqual(len(meta['cities']),26)
  for a,b in [('Hà Nội','Sa Pa'),('TP. Hồ Chí Minh','Cà Mau'),('Đà Nẵng','Đồng Hới'),('Pleiku','Kon Tum')]:
   for origin,destination in [(a,b),(b,a)]:
    trips=self.request('/trips?'+urlencode({'origin':origin,'destination':destination,'date':self.day}))[1]
    self.assertEqual(len(trips),12);self.assertEqual(len({t['departure'] for t in trips}),12)
  last=self.request('/trips?'+urlencode({'origin':'Hà Nội','destination':'Sa Pa','date':meta['maxDate']}))[1]
  self.assertEqual(len(last),12)
 def test_22_customer_registered_names(self):
  for i,name in enumerate(['Trần Thị Minh Anh','Lê Hoàng Nam']):
   p={'name':name,'email':f'identity{i}@example.com','phone':'0901234987','password':'Identity123'}
   status,registered=self.request('/register','POST',p);self.assertEqual(status,200)
   self.assertEqual(registered['user']['name'],name)
   logged=self.request('/login','POST',{'email':p['email'],'password':p['password']})[1]
   self.assertEqual(logged['user']['name'],name)
   self.assertEqual(self.request('/me',token=logged['token'])[1]['user']['name'],name)
 def test_23_seed_restart_preserves_data(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('vivu_seed_test',ROOT/'server.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.DB=self.db
  with mod.connect() as c:
   before=c.execute('SELECT count(*) FROM trips').fetchone()[0]
   original=dict(c.execute('SELECT * FROM trips WHERE id=?',(self.trips[0]['id'],)).fetchone())
   # A legacy demo account receives its neutral label without touching bookings.
   c.execute("UPDATE users SET name='Nguyễn Quang Thuận' WHERE email='khach@vivu.vn'")
   booking_count=c.execute('SELECT count(*) FROM bookings').fetchone()[0]
  mod.init()
  with mod.connect() as c:
   self.assertEqual(c.execute('SELECT count(*) FROM trips').fetchone()[0],before)
   self.assertEqual(dict(c.execute('SELECT * FROM trips WHERE id=?',(original['id'],)).fetchone()),original)
   self.assertEqual(c.execute('SELECT count(*) FROM bookings').fetchone()[0],booking_count)
   self.assertEqual(c.execute("SELECT name FROM users WHERE email='khach@vivu.vn'").fetchone()[0],'Khách trải nghiệm')
   c.execute("UPDATE users SET name='Tên tôi tự đặt' WHERE email='khach@vivu.vn'")
  mod.init()
  with mod.connect() as c:self.assertEqual(c.execute("SELECT name FROM users WHERE email='khach@vivu.vn'").fetchone()[0],'Tên tôi tự đặt')

if __name__=='__main__':unittest.main(verbosity=2)
