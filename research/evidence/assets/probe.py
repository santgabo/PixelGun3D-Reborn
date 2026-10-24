import zipfile,struct,collections,re,json,os
BASE='/Users/santgabo/Projects/PixelGun3D/'
TMP=os.path.dirname(__file__)
A=zipfile.ZipFile(BASE+'Pixel Gun 3D [11.3.1].apk'); B=zipfile.ZipFile(BASE+'main.1191.com.pixel.gun3d.obb')
def load(z,n):
 n='assets/bin/Data/'+n
 if n in z.namelist():return z.read(n)
 return b''.join(z.read(x) for x in sorted([x for x in z.namelist() if x.startswith(n+'.split')],key=lambda x:int(x.rsplit('split',1)[1])))
def parse(d):
 ms,fs,v,off=struct.unpack_from('>4I',d); assert v==15,(v,len(d));assert fs==len(d),(fs,len(d))
 o=d.index(b'\0',20)+1; engine=d[20:o-1].decode();platform,tree,nt=struct.unpack_from('<iBi',d,o);o+=9;assert tree==0
 types=[]
 for _ in range(nt):
  cid=struct.unpack_from('<i',d,o)[0];o+=4
  if cid<0 or cid==114:o+=16
  o+=16;types.append(cid)
 no=struct.unpack_from('<i',d,o)[0];o+=4;objs=[]
 for _ in range(no):
  o=(o+3)&~3;pid,start,size,tid,cid,script,stripped=struct.unpack_from('<qIIiHhB',d,o);o+=25
  assert off+start+size<=len(d)
  objs.append(dict(id=pid,offset=off+start,size=size,type=cid,tid=tid,script=script))
 return dict(engine=engine,platform=platform,types=types,objects=objs,dataOffset=off,metadataEnd=o)
def astr(d,o):
 n=struct.unpack_from('<i',d,o)[0];assert 0<=n<=len(d)-o-4,(n,o)
 return d[o+4:o+4+n].decode('utf8','replace'),(o+4+n+3)&~3
def goname(d,x):
 o=x['offset'];n=struct.unpack_from('<i',d,o)[0];assert n<10000
 return astr(d,o+4+n*16+4)[0]
def named(d,x):return astr(d,x['offset'])[0]
if __name__=='__main__':
 d=load(A,'globalgamemanagers');p=parse(d)
 for x in p['objects']:
  if x['type'] in (141,129):print('GLOBAL',x,repr(d[x['offset']:x['offset']+min(x['size'],1000)]))
 out=[]
 scenes=sorted(set(re.sub(r'\.split\d+$','',n.rsplit('/',1)[-1]) for n in B.namelist() if re.fullmatch(r'assets/bin/Data/level\d+(\.split\d+)?',n)),key=lambda n:int(n[5:]))
 for n in ['level0']+scenes:
  d=load(A if n=='level0' else B,n);p=parse(d);names=[];errors=[]
  for x in p['objects']:
   if x['type']==1:
    try:names.append(goname(d,x))
    except Exception as e:errors.append(str(e))
  row=dict(file=n,size=len(d),engine=p['engine'],counts=dict(collections.Counter(x['type'] for x in p['objects'])),names=names,errors=errors[:2]);out.append(row)
  if n in ('level0','level1','level12','level24','level104'):print('SCENE',n,row['counts'],names[:35],row['errors'])
 json.dump(out,open(TMP+'/scene-inventory.json','w'),indent=2)
 print('ALL SCENES',len(out),'written',TMP+'/scene-inventory.json')
