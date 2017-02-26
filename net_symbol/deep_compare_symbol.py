import numpy as npy
import mxnet as mx

class DeepCompareLossLayer(mx.operator.NumpyOp):
    def __init__(self):
        super(DeepCompareLossLayer, self).__init__(False)
        
    def list_arguments(self):
        return ['data','label']
        
    def list_outputs(self):
        return ['outputs']
        
    def infer_shape(self, in_shape):
        data_shape=in_shape[0]
        label_shape=(in_shape[0][0],)
        return [data_shape, label_shape],[data_shape]
        
    def forward(self, in_data, out_data):
        x=in_data[0]
        l=in_data[1]
        y=out_data[0]
        y[:]=npy.ones((x.shape[0],1))-l.reshape((x.shape[0],1))*x  
        
        
    def backward(self, out_grad, in_data, out_data, in_grad):
        l=in_data[1]
        y = out_data[0] 
        dx=in_grad[0]
        
        dx[:]=1
        dx[l>0]=-1
        dx[y<0]=0

def GetSharedConvNet(data,conv_weight, conv_bias):
    shared_net = mx.sym.Convolution(data=data, kernel=(7, 7), stride=(3,3),
                         pad=(3, 3), num_filter=96,weight=conv_weight[0],
                        bias=conv_bias[0],name="conv0")
    shared_net = mx.sym.Activation(data=shared_net, act_type="relu", name="relu0")
    shared_net = mx.sym.Pooling(data=shared_net, kernel=(2,2),pool_type="max",                           
                           stride=(2,2), name="maxpool0")
    shared_net = mx.sym.Convolution(data=shared_net, kernel=(5, 5), stride=(1,1),
                         pad=(2, 2), num_filter=192, weight=conv_weight[1],
                        bias=conv_bias[1],name="conv1")
    shared_net = mx.sym.Activation(data=shared_net, act_type="relu", name="relu1")
    shared_net = mx.sym.Pooling(data=shared_net, kernel=(2,2),pool_type="max",                           
                           stride=(2,2), name="maxpool1")
    shared_net = mx.sym.Convolution(data=shared_net, kernel=(3, 3), stride=(1,1),
                         pad=(1, 1), num_filter=256, weight=conv_weight[2],
                        bias=conv_bias[2],name="conv2")
    shared_net = mx.sym.Activation(data=shared_net, act_type="relu", name="relu2")
    return shared_net


def DeepCompareSymbolSiamese():  
    data1 = mx.sym.Variable("data1")
    data2 = mx.sym.Variable("data2")
    conv_weight = []
    conv_bias = []
    for i in range(3):
        conv_weight.append(mx.sym.Variable('conv' + str(i) + '_weight'))
        conv_bias.append(mx.sym.Variable('conv' + str(i) + '_bias'))
    conv_res1= GetSharedConvNet(data1,conv_weight, conv_bias)   
    conv_res2= GetSharedConvNet(data2,conv_weight, conv_bias)  
    conv_res=mx.sym.Concat(conv_res1,conv_res2,dim=1, name='conv_res')
    net = mx.sym.FullyConnected(data=conv_res,num_hidden=512, name="fc1")
    net = mx.sym.Activation(data=net, act_type="relu", name="relu1")
    net = mx.sym.FullyConnected(data=net,num_hidden=1, name="fc2")
    return net

def DeepCompareSymbolTwoChannel():
    data = mx.sym.Variable("data")
    net = mx.sym.Convolution(data=data, kernel=(7, 7), stride=(3,3),
                             pad=(3, 3), num_filter=96,name="conv0")
    net = mx.sym.Activation(data=net, act_type="relu", name="relu0")
    net = mx.sym.Pooling(data=net, kernel=(2,2),pool_type="max",                           
                           stride=(2,2), name="maxpool0")
    net = mx.sym.Convolution(data=net, kernel=(5, 5), stride=(1,1),
                             pad=(2, 2), num_filter=192,name="conv1")
    net = mx.sym.Activation(data=net, act_type="relu", name="relu1")
    net = mx.sym.Pooling(data=net,kernel=(2,2),pool_type="max",
                            stride=(2,2), name="maxpool1")
    net = mx.sym.Convolution(data=net, kernel=(3, 3), stride=(1,1),
                             pad=(1, 1), num_filter=256,name="conv2")
    net = mx.sym.Activation(data=net, act_type="relu", name="relu2")
    net = mx.sym.Flatten(data=net)
    net = mx.sym.FullyConnected(data=net,num_hidden=256, name="fc1")
    net = mx.sym.Activation(data=net, act_type="relu", name="relu3")
    net = mx.sym.FullyConnected(data=net,num_hidden=1, name="fc2")
    return net  
    
def VGGStackUnit(data,nfilters,idx):
    datap=data
    for k in range(3):
        datap=mx.sym.Convolution(data=datap, kernel=(3, 3), stride=(1,1),
                             pad=(1, 1), num_filter=nfilters,name="conv_s"+str(idx)+"_"+str(k)) 
        datap=mx.sym.Activation(data=datap, act_type="relu", name="relu_s"+str(idx)+"_"+str(k))
    return datap
    
 
def DeepCompareSymbolTwoChannelDeep():
    data = mx.sym.Variable("data")
    net = mx.sym.Convolution(data=data, kernel=(5, 5), stride=(3,3),
                             pad=(2, 2), num_filter=96,name="conv0")
    net=VGGStackUnit(net,96,0)
    net = mx.sym.Pooling(data=net,kernel=(2,2),pool_type="max",
                            stride=(2,2), name="maxpool0") 
    net=VGGStackUnit(net,192,1)
    net = mx.sym.Flatten(data=net)
    net = mx.sym.FullyConnected(data=net,num_hidden=1, name="fc")
    return net

def GetDeepCompareSymbol(net_type,is_train):
    if net_type=="2ch":
       net=DeepCompareSymbolTwoChannelDeep()
       if is_train:
           op_loss=DeepCompareLossLayer()
           net=op_loss(data=net,name="loss")
       return net
    if net_type=="2ch":
        net=DeepCompareSymbolSiamese()
        if is_train:
            op_loss=DeepCompareLossLayer()
            net=op_loss(data=net,name="loss")
    return net 
        
if __name__=="__main__":
    net=GetDeepCompareSymbol('2ch',True)
    ex=net.simple_bind(ctx=mx.cpu(), data=(50,2,64,64),loss_label=(50,))