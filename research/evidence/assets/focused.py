from probe import *
def extern(d,p):
 o=p['metadataEnd'];n=struct.unpack_from('<i',d,o)[0];o+=4
 for _ in range(n):o=((o+4+3)&~3)+8
 ne=struct.unpack_from('<i',d,o)[0];o+=4;out=[]
 for i in range(ne):
  o=d.index(b'\0',o)+1;o+=20;end=d.index(b'\0',o);out.append(d[o:end].decode());o=end+1
 return out
if __name__=='__main__':
 for n,z in [('globalgamemanagers',A),('globalgamemanagers.assets',A),('level104',B),('level24',B)]:
  d=load(z,n);p=parse(d);ext=extern(d,p);json.dump(ext,open(TMP+'/'+n+'.externals.json','w'),indent=2);print('EXTERNALS',n,len(ext),ext[:10])
 d=load(A,'globalgamemanagers.assets');p=parse(d);scripts={}
 for x in p['objects']:
  if x['type']==115:
   name,o=astr(d,x['offset']);o+=20;cl,o=astr(d,o);ns,o=astr(d,o);asm,o=astr(d,o);scripts[x['id']]=dict(name=name,cl=cl,ns=ns,asm=asm)
 json.dump(scripts,open(TMP+'/scripts.json','w'),indent=2)
 for n in ['level104','level24']:
  d=load(B,n);p=parse(d);ext=extern(d,p);go={x['id']:goname(d,x) for x in p['objects'] if x['type']==1};counts=collections.Counter();examples=[]
  for x in p['objects']:
   if x['type']==114:
    o=x['offset'];gid=struct.unpack_from('<q',d,o+4)[0];sf,sp=struct.unpack_from('<iq',d,o+16);sc=scripts.get(sp,{}) if sf and 'globalgamemanagers.assets' in ext[sf-1] else {};cl=sc.get('cl',str((sf,sp)));counts[cl]+=1
    if re.search('UIRoot|UIAnchor|UISprite|UILabel|UIAtlas|UIFont|Shop|MainMenu',cl):examples.append(dict(x,go=go.get(gid),script=cl,scriptptr=[sf,sp],raw=d[o+28:o+min(x['size'],120)].hex()))
  print('SCRIPT COUNTS',n,counts.most_common(45));json.dump(examples,open(TMP+'/'+n+'.ui.json','w'),indent=2);print('UI EXAMPLES',examples[:3])
 d=load(A,'globalgamemanagers');p=parse(d)
 for x in p['objects']:
  if x['type']==147:
   o=x['offset'];nc=struct.unpack_from('<i',d,o)[0];o+=4;print('RESOURCE ENTRIES',nc)
   rows=[]
   for i in range(nc):
    name,o=astr(d,o);fid,pid=struct.unpack_from('<iq',d,o);o+=12;rows.append(dict(name=name,file=fid,id=pid))
   print('RESOURCE MATCHES',[r for r in rows if re.search('mainmenu|shop|atlas|font',r['name'],re.I)][:85]);json.dump(rows,open(TMP+'/resource-map.json','w'),indent=2)
