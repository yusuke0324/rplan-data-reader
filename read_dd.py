import numpy as np 
from PIL import Image
import mask_to_poly as mr

def read_door(door_img,img,tmp_diff):
	# door_imgはbinary image
	# imgはおそらくRGB
	# 多分だけどもとのdoor imgとimgを，新しいdoor画像に書き換えてる(もっと正規化したもの．)
	# 多分だけど，ドアのラベルが与えられた画像になってる

	tmp3=door_img.copy()
	tmp4=door_img.copy()
	for k in range(256):
		for h in range(256):
			has=[]
			for knm in range(10): #knmはどこにも使ってない模様
				has.append(0)
			if(tmp4[k][h]==1): # その座標がdoorだったら
				p=img[k-tmp_diff-4:k+tmp_diff+4,h-tmp_diff-4:h+tmp_diff+4,2]
				s=p[np.nonzero(p)]
				if(len(s)==0):
					continue
				r=[]
				kmmmm=s[0] # kmmmmも使ってない．謎すぎる
				for t in range(len(s)):
					if(t==0):
						r.append(s[t])
					elif(s[t] not in r):
						r.append(s[t])
				if(len(r)>=3):
					 tmp3[k][h]=0	
				elif(len(r)==2):
					has[r[0]]=1
					has[r[1]]=1
					tmp3[k][h]= has[0]*1+has[1]*2+has[3]*4+has[4]*8+has[5]*16+has[6]*32+has[7]*64+has[8]*128+has[9]*256
	s=np.unique(tmp3)
	tmp4=tmp3.copy()
	for ks in range(len(s)):
		for k in range(256):
			for h in range(256):
				if(tmp3[k][h]==s[ks]):
					tmp4[k][h]=int(ks)
	return tmp4



def sort_corners(corners ,k_d):
	coords=[]
	ind=[]
	if(k_d==0):
		for j in range(len(corners)):
			ind.append(0)
		for i in range(len(corners)):
			if (i==0):
				coords.append(corners[0])
				ind[i]=1

			elif(i%2==1):
				k=coords[i-1][0]
				for j in range(len(corners)):
					if(corners[j][0]==k)& ( ind[j]!=1):
						coords.append(corners[j])
						ind[j]=1
						break
			elif(i%2==0):
				k=coords[i-1][1]
				for j in range(len(corners)):
					if(corners[j][1]==k)&  (ind[j]!=1):
						coords.append(corners[j])
						ind[j]=1
						break
					
	if(k_d==1):
		for s in range(len(corners)):
			ind.append(0)
		p=0		
		for i in range(len(corners)):
			if (i%4==0):
				coords.append(corners[i])
				ind[i]=1
				p=p+1
			elif(i%2==1):
				k=coords[i-1][0]
				tk=coords[i-1][1]  
				pp=0
				for j in range(len(corners)):
					if(corners[j][0]==k)& (ind[j]!=1):
						if(pp==0) :
							pp=pp+1
							coords.append(corners[j])
							fn=j
						else:
							if (abs(corners[j][1]-tk)<=abs(coords[i][1]-tk)) &(abs(corners[j][1]-tk)!=0):
								coords[i]=corners[j]
								fn=j
				ind[fn]=ind[fn]+1
				fn=-1		
				p=p+1
			elif(i%2==0)& (i%4!=0):
				p=p+1
				k=coords[i-1][1]
				tk=coords[i-1][0] 
				pp=0
				for j in range(len(corners)):
					if(corners[j][1]==k) & (ind[j]!=1):
						if(pp==0):
							pp=pp+1
							coords.append(corners[j])
							fn=j  						
						else:
							if (abs(corners[j][0]-tk)<=abs(coords[i][0]-tk)) &(abs(corners[j][0]-tk)!=0):
								coords[i]=corners[j]
								fn=j  
				ind[fn]=ind[fn]+1 
				fn=-1
	return coords
			
def read_data(line):
	''' 多分以下を返してる
		rms_type:部屋のタイプのリスト(ドア:17, エントランス:15を含む)
		poly: 各部屋の座標セットのリスト
		doors:ドアの位置を表す座標[始点X, 始点Y, 終点X, 終点Y]のリスト
		walls:壁の位置を表す座標 [始点X, 始点Y, 終点X, 終点Y, -1, 部屋タイプID, 部屋のindex, -1, 0]のリスト
		out: 処理の成功または失敗を表す整数値。1 は成功を、-1 や -3 などは異なる失敗理由を示しています。
		XとYは，画像で表示した時の軸であることに注意．通常画像に対しての座標はimg[Y, X]のようindexする
		多分左回りに左上の点から(例えば四角形なら)[左上x,左上y,左下x,左下y][左下xy, 右下xy][右下xy, 右上xy][右上xy, 左上xy]という4つで表してる

	'''
	poly=[]
	img = np.asarray(Image.open(line))
	dec=0 # スキップしたドアの数?
	img_room_type=img[:,:,1]
	img_room_number=img[:,:,2]
	wall_img=np.zeros((256, 256))
	for k in range(256):
		for h in range(256):
			if(img_room_type[k][h]==16):
				wall_img[k][h]=16		
			if(img_room_type[k][h]==17):
				wall_img[k][h]=10
	room_no=img_room_number.max()
	room_imgs=[]
	rm_types=[]
	# それぞれの部屋のタイプと部屋の画像をリストに入れる
	for i in range(room_no):
		# 部屋の画像はbinaryのマスク
		room_img=np.zeros((256, 256))
		for k in range(256):
			for h in range(256):
				if(img_room_number[k][h]==i+1):
					room_img[k][h]=1
					k_=k
					h_=h
		rm_t=img_room_type[k_][h_]

		#changing rplan rooms_type to housegan++ rooms_type
		if(rm_t==0):
			rm_types.append(1)		
		elif(rm_t==1):
			rm_types.append(3)
		elif(rm_t==2):
			rm_types.append(2)		
		elif(rm_t==3):
			rm_types.append(4)
		elif(rm_t==4):
			rm_types.append(7)
		elif(rm_t==5):
			rm_types.append(3)
		elif(rm_t==6):
			rm_types.append(8)
		elif(rm_t==7):
			rm_types.append(3)
		elif(rm_t==8):
			rm_types.append(3)
		elif(rm_t==9):
			rm_types.append(5)
		elif(rm_t==10):
			rm_types.append(6)
		elif(rm_t==11):
			rm_types.append(10)
		else:
			rm_types.append(16)
		room_imgs.append(room_img)

	walls=[]
	doors=[]
	rm_type=rm_types
	# room_imgs内の各部屋画像に対して、周囲の壁を修正する
	for t in range(len(room_imgs)):
		tmp=room_imgs[t]
		for k in range(254):
			for h in range(254):
				if(tmp[k][h]==1) & (tmp[k+1][h]==0) & (tmp[k+2][h]==1):
					tmp[k+1][h] =1				
		for k in range(254):
			for h in range(254):
				if(tmp[h][k]==1) & (tmp[h][k+1]==0) & (tmp[h][k+2]==1):
					tmp[h][k+1] =1				
		for k in range(254):
			for h in range(254):
				if(tmp[k][h]==0) & (tmp[k+1][h]==1) & (tmp[k+2][h]==0):
					tmp[k+1][h] =0				
		for k in range(254):
			for h in range(254):
				if(tmp[h][k]==0) & (tmp[h][k+1]==1) & (tmp[h][k+2]==0):
					tmp[h][k+1] =0

		room_imgs[t]=tmp
		# 部屋のポリゴン取得
		poly2=mr.get_polygon(room_imgs[t])
		# LinearRing の各頂点の座標を含むイテラブル（通常はタプルのシーケンス）です。各タプルは (x, y) の形式（2次元の場合
		coords_1=list(poly2.exterior.coords)
		coords=[]
		for kn in range(len(coords_1)):
			# [y, x, 0, 0, t, rm_type[t]] に変換．tは部屋番号とrm_type[t]は部屋の種別ID
			coords.append([list(coords_1[kn])[1],list(coords_1[kn])[0],0,0,t,rm_type[t]]) 
		p=0
		for c in range(len(coords)-1):
			# [始Y, 始X, 終Y, 終X, -1, 部屋タイプID, 部屋のindex, -1, 0]
			walls.append([coords[c][0],coords[c][1],coords[c+1][0],coords[c+1][1],-1,coords[c][5],coords[c][4],-1,0])
		p=len(coords)-1
		poly.append(p)
	# imgは最初のnp array
	# channel1には部屋の種別が入ってる	
	tmp=img[:,:,1]


	# こっからはドア
	door_img=np.zeros((256, 256))
	doors_img=[]		
	for k in range(256):
		for h in range(256):
			if(tmp[k][h]==17): # 17がドアっぽい
				door_img[k][h]=1
	
	tmp=door_img
	rms_type=rm_type
	coords=[]
	for k in range(2,254):
		for h in range(2,254):
			if(tmp[k][h]==1):
				# コーナーを探してるのかも
				if((tmp[k-1][h]==0) & (tmp[k-1][h-1]==0)&(tmp[k][h-1]==0)):
					coords.append([h,k,0,0])
				elif (tmp[k+1][h]==0)&(tmp[k+1][h-1]==0)&(tmp[k][h-1]==0):
					coords.append([h,k,0,0])
				elif (tmp[k+1][h]==0)&(tmp[k+1][h+1]==0)&(tmp[k][h+1]==0): 
					coords.append([h,k,0,0])
				elif (tmp[k-1][h]==0)&(tmp[k-1][h+1]==0)&(tmp[k][h+1]==0): 
					coords.append([h,k,0,0])					
				elif(tmp[k+1][h]==1)&(tmp[k][h+1]==1)& (tmp[k+1][h+1]==0):
					coords.append([h,k,0,0])					
				elif(tmp[k-1][h]==1)&(tmp[k][h+1]==1)& (tmp[k-1][h+1]==0):
					coords.append([h,k,0,0])					
				elif(tmp[k+1][h]==1)&(tmp[k][h-1]==1)&(tmp[k+1][h-1]==0) : 
					coords.append([h,k,0,0])				
				elif(tmp[k-1][h]==1) & (tmp[k][h-1]==1) & (tmp[k-1][h-1]==0):
					coords.append([h,k,0,0])
	# 最小距離を見つけるための比較基準?		
	tmp_diff=1000000   
	p_x_1=coords[0][0]
	# coords リストの最初の座標から始めて、リスト内の他の全ての座標とのX軸における距離を計算し、その最小値を tmp_diff に更新
	for k in range(1, len(coords)):
		p_x_2=coords[k][0]
		tmp_dif=abs(p_x_1-p_x_2)
		if(tmp_dif<tmp_diff)&(tmp_dif>1):
			tmp_diff=tmp_dif
	p_y_1=coords[0][1]
	# どうようにy軸での最小値も
	for k in range(1, len(coords)):
		p_y_2=coords[k][1]
		tmp_dif=abs(p_y_1-p_y_2)
		if(tmp_dif<tmp_diff)&(tmp_dif>1):
			tmp_diff=tmp_dif
	
	door_imgs=read_door(door_img,img,tmp_diff)
	door_no=int(door_imgs.max())
	door_tp=[]
	for i in range(door_no): # 各ドアに対してdoor_imgを作る．部屋と同じ感じだ
		door_img=np.zeros((256, 256))
		for k in range(256):
			for h in range(256):
				if(door_imgs[k][h]==i+1):door_img[k][h]=1
		doors_img.append(door_img)
	rmpn=len(doors_img)				
	for t in range(len(doors_img)):
		tmp=doors_img[t]
		kpp=np.max(tmp)
		if(kpp<=0): # 画像の有効性チェック．0以下な場合はスキップ．
			dec=dec+1
			continue
		poly2=mr.get_polygon(doors_img[t]) # 画像からポリゴン生成
		coords_1=list(poly2.exterior.coords)#
		coords=[]
		for kn in range(len(coords_1)):
			coords.append([list(coords_1[kn])[1],list(coords_1[kn])[0],0,0,t,17]) 
		p=0
		for c in range(len(coords)-1):
			# [始Y,始X,終Y,終X, -1, 17, 多分ドアのindex?,-1, 0] 
			walls.append([coords[c][0],coords[c][1],coords[c+1][0],coords[c+1][1],-1,17,len(rms_type)+coords[c][4]-dec,-1,0])
			doors.append([coords[c][0],coords[c][1],coords[c+1][0],coords[c+1][1]])
		p=len(coords)-1
		poly.append(p)
	

	# ==ここからはエントランス=====
	tmp=img[:,:,1]
	en_img=np.zeros((256, 256))
	for k in range(256):
		for h in range(256):
			if(tmp[k][h]==15): # 15がエントランス？
				en_img[k][h]=1
	tmp=en_img
	coords=[]
	for k in range(2,254):
		for h in range(2,254):
			if(tmp[k][h]==1):
				if((tmp[k-1][h]==0) & (tmp[k-1][h-1]==0)&(tmp[k][h-1]==0)):
					coords.append([h,k,0,0])
				elif (tmp[k+1][h]==0)&(tmp[k+1][h-1]==0)&(tmp[k][h-1]==0):
					coords.append([h,k,0,0])
				elif (tmp[k+1][h]==0)&(tmp[k+1][h+1]==0)&(tmp[k][h+1]==0): 
					coords.append([h,k,0,0])
				elif (tmp[k-1][h]==0)&(tmp[k-1][h+1]==0)&(tmp[k][h+1]==0): 
					coords.append([h,k,0,0])
				elif(tmp[k+1][h]==1)&(tmp[k][h+1]==1)& (tmp[k+1][h+1]==0):
					coords.append([h,k,0,0])					
				elif(tmp[k-1][h]==1)&(tmp[k][h+1]==1)& (tmp[k-1][h+1]==0):
					coords.append([h,k,0,0])					
				elif(tmp[k+1][h]==1)&(tmp[k][h-1]==1)&(tmp[k+1][h-1]==0) : 
					coords.append([h,k,0,0])					
				elif(tmp[k-1][h]==1) & (tmp[k][h-1]==1) & (tmp[k-1][h-1]==0):
					coords.append([h,k,0,0])
					
	en_imgs=[]
	for i in range(1):

		door_img=np.zeros((256, 256))
		for k in range(256):
			for h in range(256):
				if(en_img[k][h]==i+1):
					en_img[k][h]=1
		en_imgs.append(en_img)
	for t in range(len(en_imgs)):
		tmp=en_imgs[t]
		kpp=np.max(tmp)
		if(kpp<=0):
			dec=dec+1
			continue
		poly2=mr.get_polygon(en_imgs[t])
		coords_1=list(poly2.exterior.coords)
		coords=[]
		for kn in range(len(coords_1)):
			coords.append([list(coords_1[kn])[1],list(coords_1[kn])[0],0,0,t,15]) 
		p=0
		for c in range(len(coords)-1):
			walls.append([coords[c][0],coords[c][1],coords[c+1][0],coords[c+1][1],-1,15,rmpn+len(rms_type)+coords[c][4]-dec,-1,0])
			doors.append([coords[c][0],coords[c][1],coords[c+1][0],coords[c+1][1]])
		p=len(coords)-1
		poly.append(p)
	
	no_doors=int(len(doors)/4)
	rms_type=rm_type
	for i in range(no_doors-1):
		rms_type.append(17)
	rms_type.append(15)
	out=1
	### check if it was noy polygon 
	for i in range(len(poly)):
		if(poly[i]<4):
			out=-1
	if (len(doors)%4!=0):
			out=-3	
	##saving the name out standard (usable) layout		
	# if(out!=1):
	# 	h.write(line)
	"""f=open("output.txt", "a+")
	f.write(str(rms_type).strip('[]'))
	f.write("   ")
	f.write(str(len(rms_type)))
	if((len(rms_type)-no_doors)>(no_doors)):
		h1=open("door.txt","a+")
		out=-4	
		h1.write(line)"""
	assert(out==1), f"error in reading the file {line}, {out=} but expected out==1"
	return rms_type,poly,doors,walls,out
	
