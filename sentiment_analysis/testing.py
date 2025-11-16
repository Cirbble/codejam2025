x=["1","2","3","4","5"]
z=[1,2,3,4,5]
y= (int(i) for i in x if i.isnumeric())
print(list(y))
print(list(str(i) for i in z))