import numpy as np
from shapely import geometry as geo

cts = [[[1,1,0],[1,1,0],[0,0,0]], [[1,1,1],[1,1,1],[1,1,0]], [[0,0,1],[0,1,1],[0,1,1]], [[0,0,0],[0,1,1],[1,1,1]]]
cts = [[np.rot90(c, 0), np.rot90(c,1), np.rot90(c,2), np.rot90(c,3)] for c in cts]
cts = np.array(cts)
def is_contour(tmp, x):
    c = tmp[x[0]-1:x[0]+2, x[1]-1:x[1]+2]
    if(np.sum(c) not in [4,5,8]):
        return False
    for i in range(4):
        for j in range(4):
            if(np.array_equal(c , cts[j,i,:,:])):
                return True
    return False

def corner_type(tmp, c):
    # その点の輪郭パターンを返す．
    # 輪郭のパターン(cts)とどう一致するか
    c = tmp[c[0]-1:c[0]+2, c[1]-1:c[1]+2]

    for i in range(4):
        if(np.array_equal(c, cts[0,i])):
            return (i+2)%4
    for i in range(4):
        if(np.array_equal(c, cts[1,i])):
            return (i+1)%4
    for i in range(4):
        if(np.array_equal(c, cts[2,i])):
            return (i)%4
    for i in range(4):
        if(np.array_equal(c, cts[3,i])):
            return (i)%4
    assert False, "Corner type is not supported"

def preprocess(tmp):
    # maskの穴を消したりしてる感じ？
    #以下のパターンに一致する場合，p1~p3は中央のピクセスを0にする.p4は0のところを1にする
    # (さらにこれらを4回90度に回転してる)
    # 例えばp4なら
    #111
    #111
    #101
# その周囲には直線の途中であることを示すピクセルが存在します。このようなピクセルは、物体の輪郭から外れた部分であり、輪郭検出の際に不要な情報となります。そのため、中央のピクセルを 0 に設定することで、このような余分な部分を取り除き、輪郭の正確性を向上させることができます
    p1 = np.array([[0,1,1],[0,1,0],[0,0,0]])
    p2 = np.array([[1,1,0],[0,1,0],[0,0,0]])
    p3 = np.array([[1,1,1],[0,1,1],[0,0,1]])
    p4 = np.array([[1,1,1],[1,1,1],[1,0,1]])
    pts = np.transpose(np.where(tmp > 0))
    for p in pts:
        # pts リスト内の各ピクセル座標 p について、その周囲の3x3の領域を c として取得します
        c = tmp[p[0]-1:p[0]+2, p[1]-1:p[1]+2]
        # 取得した領域 c のピクセルの合計値が [3, 6, 8] のいずれかである場合、そのピクセルはパターンの一部として扱われ、処理が続行されます。
        if(np.sum(c) not in [3,8,6]):
            continue
        for i in range(4):
            if(np.array_equal(c, np.rot90(p1,i))):
                # 中央の値を0にする?
                tmp[p[0],p[1]]=0
            elif(np.array_equal(c, np.rot90(p2,i))):
                tmp[p[0],p[1]]=0
            elif(np.array_equal(c, np.rot90(p3,i))):
                tmp[p[0],p[1]]=0
            elif(np.array_equal(c, np.rot90(p4,i))):
                tmp[p[0]-1:p[0]+2, p[1]-1:p[1]+2] = 1

def sort_points(tmp, pts):
    # 点を特定の順でソートする
    # tmpにおける各点の位置関係に基づく連続した輪郭線を形成するために使用
    points = [pts[0]]
    temp = pts[0]
    while(len(pts)>len(points)):
        # tempの輪郭パターン
        ct = corner_type(tmp, temp)

        offset = [0,0]
        if(ct==3):
            candids = [p for p in pts if(p[0]==temp[0] and p[1]<temp[1])]
            diff = np.array([temp[1]-p[1] for p in candids])
            candid = candids[np.argmin(diff)]
            if(candid[0]-temp[0]!=0):
                offset[0] = temp[0] - candid[0]
        if(ct==0):
            candids = [p for p in pts if(p[1]==temp[1] and p[0]>temp[0])]
            diff = np.array([p[0]-temp[0] for p in candids])
            candid = candids[np.argmin(diff)]
            if(candid[1]-temp[1]!=0):
                offset[1] = temp[1] - candid[1]
        if(ct==1):
            candids = [p for p in pts if(p[0]==temp[0] and p[1]>temp[1])]
            diff = np.array([p[1]-temp[1] for p in candids])
            candid = candids[np.argmin(diff)]
            if(candid[0]-temp[0]!=0):
                offset[0] = temp[0] - candid[0]
        if(ct==2):
            candids = [p for p in pts if(p[1]==temp[1] and p[0]<temp[0])]
            diff = np.array([temp[0]-p[0] for p in candids])
            candid = candids[np.argmin(diff)]
            if(candid[1]-temp[1]!=0):
                offset[1] = temp[1] - candid[1]
        temp = candid
        points = points + [temp+offset]
    points = np.array(points)
    return points;


def get_polygon(mask):
    preprocess(mask)
    # np.where からの出力は (array([行インデックス]), array([列インデックス])) の形式であり、これは複数の座標点を扱う際に直接使いにくい
    # これによって各行が (x, y) 座標ペア
    pts = np.transpose(np.where(mask>0))
    #print("point is",pts) 
    pts = [x for x in pts if is_contour(mask, x)]
    # sort_points 関数で座標点をソートする必要があるのは、画像中の輪郭や境界を形成する点を正しい順序で並べ、それらを結ぶことで幾何学的に正確なポリゴンや他の形状を作成するため
    pts = sort_points(mask, pts)
    # geo.Polygon は、Python の shapely ライブラリに含まれているクラスで、2次元の座標点のリストを入力として、それらの点を頂点とするポリゴン（多角形）を生成
    poly = geo.Polygon(pts)
    return poly

