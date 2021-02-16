# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/100_models.layers.ipynb (unless otherwise specified).

__all__ = ['noop', 'init_lin_zero', 'lin_zero_init', 'SwishBeta', 'same_padding1d', 'Pad1d', 'Conv1dSame',
           'same_padding2d', 'Pad2d', 'Conv2dSame', 'Conv2d', 'Chomp1d', 'Conv1dCausal', 'Conv1d', 'SeparableConv1d',
           'AddCoords1d', 'ConvBlock', 'Conv', 'ConvBN', 'ConvIN', 'CoordConv', 'CoordConvBN', 'SepConv', 'SepConvBN',
           'SepConvIN', 'SepCoordConv', 'SepCoordConvBN', 'ResBlock1dPlus', 'SEModule1d', 'Norm', 'BN1d', 'IN1d',
           'LinLnDrop', 'LambdaPlus', 'Squeeze', 'Unsqueeze', 'Add', 'Concat', 'Permute', 'Transpose', 'View',
           'Reshape', 'Max', 'LastStep', 'SoftMax', 'Noop', 'Sharpen', 'Sequential', 'TimeDistributed', 'Temp_Scale',
           'Vector_Scale', 'Matrix_Scale', 'get_calibrator', 'LogitAdjustmentLayer', 'LogitAdjLayer', 'PPV', 'PPAuc',
           'MaxPPVPool1d', 'AdaptiveWeightedAvgPool1d', 'GAP1d', 'GACP1d', 'GAWP1d', 'GlobalWeightedAveragePool1d',
           'gwa_pool_head', 'GWAP1d', 'AttentionalPool1d', 'GAttP1d', 'attentional_pool_head', 'create_pool_head',
           'pool_head', 'average_pool_head', 'concat_pool_head', 'max_pool_head', 'create_pool_plus_head',
           'pool_plus_head', 'create_conv_head', 'conv_head', 'create_mlp_head', 'mlp_head', 'create_fc_head',
           'fc_head', 'create_rnn_head', 'rnn_head', 'create_conv_lin_3d_head', 'conv_lin_3d_head',
           'create_lin_3d_head', 'lin_3d_head', 'universal_pool_head', 'heads', 'SqueezeExciteBlock', 'GaussianNoise',
           'gambler_loss', 'CrossEntropyLossOneHot', 'ttest_bin_loss', 'ttest_reg_loss', 'CenterLoss', 'CenterPlusLoss',
           'FocalLoss', 'TweedieLoss']

# Cell
from torch.nn.init import normal_
from fastai.torch_core import Module
from fastai.layers import *
from torch.nn.utils import weight_norm, spectral_norm
from ..imports import *
from ..utils import *

# Cell
def noop(x): return x

# Cell
def init_lin_zero(m):
    if isinstance(m, (nn.Linear)):
        if getattr(m, 'bias', None) is not None: nn.init.constant_(m.bias, 0)
        nn.init.constant_(m.weight, 0)
    for l in m.children(): init_lin_zero(l)

lin_zero_init = init_lin_zero

# Cell
class SwishBeta(Module):
    def __init__(self, beta=1.):
        self.sigmoid = torch.sigmoid
        self.beta = nn.Parameter(torch.Tensor(1).fill_(beta).to(default_device()))
    def forward(self, x): return x.mul(self.sigmoid(x*self.beta))

# Cell
def same_padding1d(seq_len, ks, stride=1, dilation=1):
    "Same padding formula as used in Tensorflow"
    p = (seq_len - 1) * stride + (ks - 1) * dilation + 1 - seq_len
    return p // 2, p - p // 2


class Pad1d(nn.ConstantPad1d):
    def __init__(self, padding, value=0.):
        super().__init__(padding, value)


@delegates(nn.Conv1d)
class Conv1dSame(Module):
    "Conv1d with padding='same'"
    def __init__(self, ni, nf, ks=3, stride=1, dilation=1, **kwargs):
        self.ks, self.stride, self.dilation = ks, stride, dilation
        self.conv1d_same = nn.Conv1d(ni, nf, ks, stride=stride, dilation=dilation, **kwargs)
        self.weight = self.conv1d_same.weight
        self.bias = self.conv1d_same.bias
        self.pad = Pad1d

    def forward(self, x):
        self.padding = same_padding1d(x.shape[-1], self.ks, dilation=self.dilation) #stride=self.stride not used in padding calculation!
        return self.conv1d_same(self.pad(self.padding)(x))

# Cell
def same_padding2d(H, W, ks, stride=(1, 1), dilation=(1, 1)):
    "Same padding formula as used in Tensorflow"
    if isinstance(ks, Integral): ks = (ks, ks)
    if ks[0] == 1:  p_h = 0
    else:  p_h = (H - 1) * stride[0] + (ks[0] - 1) * dilation[0] + 1 - H
    if ks[1] == 1:  p_w = 0
    else:  p_w = (W - 1) * stride[1] + (ks[1] - 1) * dilation[1] + 1 - W
    return (p_w // 2, p_w - p_w // 2, p_h // 2, p_h - p_h // 2)


class Pad2d(nn.ConstantPad2d):
    def __init__(self, padding, value=0.):
        super().__init__(padding, value)


@delegates(nn.Conv2d)
class Conv2dSame(Module):
    "Conv2d with padding='same'"
    def __init__(self, ni, nf, ks=(3, 3), stride=(1, 1), dilation=(1, 1), **kwargs):
        if isinstance(ks, Integral): ks = (ks, ks)
        if isinstance(stride, Integral): stride = (stride, stride)
        if isinstance(dilation, Integral): dilation = (dilation, dilation)
        self.ks, self.stride, self.dilation = ks, stride, dilation
        self.conv2d_same = nn.Conv2d(ni, nf, ks, stride=stride, dilation=dilation, **kwargs)
        self.weight = self.conv2d_same.weight
        self.bias = self.conv2d_same.bias
        self.pad = Pad2d

    def forward(self, x):
        self.padding = same_padding2d(x.shape[-2], x.shape[-1], self.ks, dilation=self.dilation) #stride=self.stride not used in padding calculation!
        return self.conv2d_same(self.pad(self.padding)(x))


@delegates(nn.Conv2d)
def Conv2d(ni, nf, kernel_size=None, ks=None, stride=1, padding='same', dilation=1, init='auto', bias_std=0.01, **kwargs):
    "conv1d layer with padding='same', 'valid', or any integer (defaults to 'same')"
    assert not (kernel_size and ks), 'use kernel_size or ks but not both simultaneously'
    assert kernel_size is not None or ks is not None, 'you need to pass a ks'
    kernel_size = kernel_size or ks
    if padding == 'same':
        conv = Conv2dSame(ni, nf, kernel_size, stride=stride, dilation=dilation, **kwargs)
    elif padding == 'valid': conv = nn.Conv2d(ni, nf, kernel_size, stride=stride, padding=0, dilation=dilation, **kwargs)
    else: conv = nn.Conv2d(ni, nf, kernel_size, stride=stride, padding=padding, dilation=dilation, **kwargs)
    init_linear(conv, None, init=init, bias_std=bias_std)
    return conv

# Cell
class Chomp1d(nn.Module):
    def __init__(self, chomp_size):
        super(Chomp1d, self).__init__()
        self.chomp_size = chomp_size

    def forward(self, x):
        return x[:, :, :-self.chomp_size].contiguous()

# Cell
# Modified from https://github.com/locuslab/TCN/blob/master/TCN/tcn.py
class Conv1dCausal(Module):
    def __init__(self, ni, nf, ks, stride=1, dilation=1, **kwargs):
        padding = (ks - 1) * dilation
        self.conv_causal = nn.Conv1d(ni, nf, ks, stride=stride, padding=padding, dilation=dilation, **kwargs)
        self.weight = self.conv_causal.weight
        self.bias = self.conv_causal.bias
        self.chomp_size = padding

    def forward(self, x):
        x = self.conv_causal(x)
        return x[..., :-self.chomp_size].contiguous()

# Cell
@delegates(nn.Conv1d)
def Conv1d(ni, nf, kernel_size=None, ks=None, stride=1, padding='same', dilation=1, init='auto', bias_std=0.01, **kwargs):
    "conv1d layer with padding='same', 'causal', 'valid', or any integer (defaults to 'same')"
    assert not (kernel_size and ks), 'use kernel_size or ks but not both simultaneously'
    assert kernel_size is not None or ks is not None, 'you need to pass a ks'
    kernel_size = kernel_size or ks
    if padding == 'same':
        if kernel_size%2==1:
            conv = nn.Conv1d(ni, nf, kernel_size, stride=stride, padding=kernel_size//2 * dilation, dilation=dilation, **kwargs)
        else:
            conv = Conv1dSame(ni, nf, kernel_size, stride=stride, dilation=dilation, **kwargs)
    elif padding == 'causal': conv = Conv1dCausal(ni, nf, kernel_size, stride=stride, dilation=dilation, **kwargs)
    elif padding == 'valid': conv = nn.Conv1d(ni, nf, kernel_size, stride=stride, padding=0, dilation=dilation, **kwargs)
    else: conv = nn.Conv1d(ni, nf, kernel_size, stride=stride, padding=padding, dilation=dilation, **kwargs)
    init_linear(conv, None, init=init, bias_std=bias_std)
    return conv

# Cell
class SeparableConv1d(Module):
    def __init__(self, ni, nf, ks, stride=1, padding='same', dilation=1, bias=True, bias_std=0.01):
        self.depthwise_conv = Conv1d(ni, ni, ks, stride=stride, padding=padding, dilation=dilation, groups=ni, bias=bias)
        self.pointwise_conv = nn.Conv1d(ni, nf, 1, stride=1, padding=0, dilation=1, groups=1, bias=bias)
        if bias:
            if bias_std != 0:
                normal_(self.depthwise_conv.bias, 0, bias_std)
                normal_(self.pointwise_conv.bias, 0, bias_std)
            else:
                self.depthwise_conv.bias.data.zero_()
                self.pointwise_conv.bias.data.zero_()

    def forward(self, x):
        x = self.depthwise_conv(x)
        x = self.pointwise_conv(x)
        return x

# Cell
class AddCoords1d(Module):
    """Add coordinates to ease position identification without modifying mean and std"""
    def forward(self, x):
        bs, _, seq_len = x.shape
        cc = torch.linspace(-1,1,x.shape[-1]).repeat(bs, 1, 1).to(x.device)
        cc = (cc - cc.mean()) / cc.std()
        x = torch.cat([x, cc], dim=1)
        return x

# Cell
class ConvBlock(nn.Sequential):
    "Create a sequence of conv1d (`ni` to `nf`), activation (if `act_cls`) and `norm_type` layers."
    def __init__(self, ni, nf, kernel_size=None, ks=3, stride=1, padding='same', bias=None, bias_std=0.01, norm='Batch', zero_norm=False, bn_1st=True,
                 act=nn.ReLU, act_kwargs={}, init='auto', dropout=0., xtra=None, coord=False, separable=False,  **kwargs):
        kernel_size = kernel_size or ks
        ndim = 1
        layers = [AddCoords1d()] if coord else []
        norm_type = getattr(NormType,f"{snake2camel(norm)}{'Zero' if zero_norm else ''}") if norm is not None else None
        bn = norm_type in (NormType.Batch, NormType.BatchZero)
        inn = norm_type in (NormType.Instance, NormType.InstanceZero)
        if bias is None: bias = not (bn or inn)
        if separable: conv = SeparableConv1d(ni + coord, nf, ks=kernel_size, bias=bias, stride=stride, padding=padding, **kwargs)
        else: conv = Conv1d(ni + coord, nf, ks=kernel_size, bias=bias, stride=stride, padding=padding, **kwargs)
        act = None if act is None else act(**act_kwargs)
        if not separable: init_linear(conv, act, init=init, bias_std=bias_std)
        if   norm_type==NormType.Weight:   conv = weight_norm(conv)
        elif norm_type==NormType.Spectral: conv = spectral_norm(conv)
        layers += [conv]
        act_bn = []
        if act is not None: act_bn.append(act)
        if bn: act_bn.append(BatchNorm(nf, norm_type=norm_type, ndim=ndim))
        if inn: act_bn.append(InstanceNorm(nf, norm_type=norm_type, ndim=ndim))
        if bn_1st: act_bn.reverse()
        if dropout: layers += [nn.Dropout(dropout)]
        layers += act_bn
        if xtra: layers.append(xtra)
        super().__init__(*layers)

Conv = partial(ConvBlock, norm=None, act=None)
ConvBN = partial(ConvBlock, norm='Batch', act=None)
ConvIN = partial(ConvBlock, norm='Instance', act=None)
CoordConv = partial(ConvBlock, norm=None, act=None, coord=True)
CoordConvBN = partial(ConvBlock, norm='Batch', act=None, coord=True)
SepConv = partial(ConvBlock, norm=None, act=None, separable=True)
SepConvBN = partial(ConvBlock, norm='Batch', act=None, separable=True)
SepConvIN = partial(ConvBlock, norm='Instance', act=None, separable=True)
SepCoordConv = partial(ConvBlock, norm=None, act=None, coord=True, separable=True)
SepCoordConvBN = partial(ConvBlock, norm='Batch', act=None, coord=True, separable=True)

# Cell
class ResBlock1dPlus(Module):
    "Resnet block from `ni` to `nh` with `stride`"
    @delegates(ConvLayer.__init__)
    def __init__(self, expansion, ni, nf, coord=False, stride=1, groups=1, reduction=None, nh1=None, nh2=None, dw=False, g2=1,
                 sa=False, sym=False, norm='Batch', zero_norm=True, act_cls=defaults.activation, ks=3,
                 pool=AvgPool, pool_first=True, **kwargs):
        if nh2 is None: nh2 = nf
        if nh1 is None: nh1 = nh2
        nf,ni = nf*expansion,ni*expansion
        k0 = dict(norm=norm, zero_norm=False, act=act_cls, **kwargs)
        k1 = dict(norm=norm, zero_norm=zero_norm, act=None, **kwargs)
        convpath  = [ConvBlock(ni,  nh2, ks, coord=coord, stride=stride, groups=ni if dw else groups, **k0),
                     ConvBlock(nh2,  nf, ks, coord=coord, groups=g2, **k1)
        ] if expansion == 1 else [
                     ConvBlock(ni,  nh1, 1, coord=coord, **k0),
                     ConvBlock(nh1, nh2, ks, coord=coord, stride=stride, groups=nh1 if dw else groups, **k0),
                     ConvBlock(nh2,  nf, 1, coord=coord, groups=g2, **k1)]
        if reduction: convpath.append(SEModule(nf, reduction=reduction, act_cls=act_cls))
        if sa: convpath.append(SimpleSelfAttention(nf,ks=1,sym=sym))
        self.convpath = nn.Sequential(*convpath)
        idpath = []
        if ni!=nf: idpath.append(ConvBlock(ni, nf, 1, coord=coord, act=None, **kwargs))
        if stride!=1: idpath.insert((1,0)[pool_first], pool(stride, ndim=1, ceil_mode=True))
        self.idpath = nn.Sequential(*idpath)
        self.act = defaults.activation(inplace=True) if act_cls is defaults.activation else act_cls()

    def forward(self, x): return self.act(self.convpath(x) + self.idpath(x))

# Cell
def SEModule1d(ni, reduction=16, act=nn.ReLU, act_kwargs={}):
    "Squeeze and excitation module for 1d"
    nf = math.ceil(ni//reduction/8)*8
    assert nf != 0, 'nf cannot be 0'
    return SequentialEx(nn.AdaptiveAvgPool1d(1),
                        ConvBlock(ni, nf, ks=1, norm=None, act=act, act_kwargs=act_kwargs),
                        ConvBlock(nf, ni, ks=1, norm=None, act=nn.Sigmoid), ProdLayer())

# Cell
def Norm(nf, ndim=1, norm='Batch', zero_norm=False, init=True, **kwargs):
    "Norm layer with `nf` features and `ndim` with auto init."
    assert 1 <= ndim <= 3
    nl = getattr(nn, f"{snake2camel(norm)}Norm{ndim}d")(nf, **kwargs)
    if nl.affine and init:
        nl.bias.data.fill_(1e-3)
        nl.weight.data.fill_(0. if zero_norm else 1.)
    return nl

BN1d = partial(Norm, ndim=1, norm='Batch')
IN1d = partial(Norm, ndim=1, norm='Instance')

# Cell
class LinLnDrop(nn.Sequential):
    "Module grouping `LayerNorm1d`, `Dropout` and `Linear` layers"
    def __init__(self, n_in, n_out, ln=True, p=0., act=None, lin_first=False):
        layers = [nn.LayerNorm(n_out if lin_first else n_in)] if ln else []
        if p != 0: layers.append(nn.Dropout(p))
        lin = [nn.Linear(n_in, n_out, bias=not ln)]
        if act is not None: lin.append(act)
        layers = lin+layers if lin_first else layers+lin
        super().__init__(*layers)

# Cell
class LambdaPlus(Module):
    def __init__(self, func, *args, **kwargs): self.func,self.args,self.kwargs=func,args,kwargs
    def forward(self, x): return self.func(x, *self.args, **self.kwargs)

# Cell
class Squeeze(Module):
    def __init__(self, dim=-1): self.dim = dim
    def forward(self, x): return x.squeeze(dim=self.dim)
    def __repr__(self): return f'{self.__class__.__name__}(dim={self.dim})'


class Unsqueeze(Module):
    def __init__(self, dim=-1): self.dim = dim
    def forward(self, x): return x.unsqueeze(dim=self.dim)
    def __repr__(self): return f'{self.__class__.__name__}(dim={self.dim})'


class Add(Module):
    def forward(self, x, y): return x.add(y)
    def __repr__(self): return f'{self.__class__.__name__}'


class Concat(Module):
    def __init__(self, dim=1): self.dim = dim
    def forward(self, *x): return torch.cat(*x, dim=self.dim)
    def __repr__(self): return f'{self.__class__.__name__}(dim={self.dim})'


class Permute(Module):
    def __init__(self, *dims): self.dims = dims
    def forward(self, x): return x.permute(self.dims)
    def __repr__(self): return f"{self.__class__.__name__}(dims={', '.join([str(d) for d in self.dims])})"


class Transpose(Module):
    def __init__(self, *dims, contiguous=False): self.dims, self.contiguous = dims, contiguous
    def forward(self, x):
        if self.contiguous: return x.transpose(*self.dims).contiguous()
        else: return x.transpose(*self.dims)
    def __repr__(self):
        if self.contiguous: return f"{self.__class__.__name__}(dims={', '.join([str(d) for d in self.dims])}).contiguous()"
        else: return f"{self.__class__.__name__}({', '.join([str(d) for d in self.dims])})"


class View(Module):
    def __init__(self, *shape): self.shape = shape
    def forward(self, x): return x.view(x.shape[0], *self.shape)
    def __repr__(self): return f"{self.__class__.__name__}({', '.join(['bs'] + [str(s) for s in self.shape])})"


class Reshape(Module):
    def __init__(self, *shape): self.shape = shape
    def forward(self, x): return x.reshape(x.shape[0], *self.shape)
    def __repr__(self): return f"{self.__class__.__name__}({', '.join(['bs'] + [str(s) for s in self.shape])})"


class Max(Module):
    def __init__(self, dim=None, keepdim=False): self.dim, self.keepdim = dim, keepdim
    def forward(self, x): return x.max(self.dim, keepdim=self.keepdim)[0]
    def __repr__(self): return f'{self.__class__.__name__}(dim={self.dim}, keepdim={self.keepdim})'


class LastStep(Module):
    def forward(self, x): return x[..., -1]
    def __repr__(self): return f'{self.__class__.__name__}()'


class SoftMax(Module):
    "SoftMax layer"
    def __init__(self, dim=-1):
        self.dim = dim
    def forward(self, x):
        return F.softmax(x, dim=self.dim)
    def __repr__(self): return f'{self.__class__.__name__}(dim={self.dim})'

Noop = nn.Sequential()

# Cell
class Sharpen(Module):
    "This is used to increase confidence in predictions - MixMatch paper"
    def __init__(self, T=.5): self.T = T
    def forward(self, x):
        x = x**(1. / self.T)
        return x / x.sum(dim=1, keepdims=True)

# Cell
class Sequential(nn.Sequential):
    """Class that allows you to pass one or multiple inputs"""
    def forward(self, *x):
        for i, module in enumerate(self._modules.values()):
            x = module(*x) if isinstance(x, (list, tuple, L)) else module(x)
        return x

# Cell
class TimeDistributed(nn.Module):
    def __init__(self, module, batch_first=False):
        super(TimeDistributed, self).__init__()
        self.module = module
        self.batch_first = batch_first

    def forward(self, x):

        if len(x.size()) <= 2:
            return self.module(x)

        # Squash samples and timesteps into a single axis
        x_reshape = x.contiguous().view(-1, x.size(-1))  # (samples * timesteps, input_size)

        y = self.module(x_reshape)

        # We have to reshape Y
        if self.batch_first:
            y = y.contiguous().view(x.size(0), -1, y.size(-1))  # (samples, timesteps, output_size)
        else:
            y = y.view(-1, x.size(1), y.size(-1))  # (timesteps, samples, output_size)

        return y

# Cell
class Temp_Scale(Module):
    "Used to perform Temperature Scaling (dirichlet=False) or Single-parameter Dirichlet calibration (dirichlet=True)"
    def __init__(self, temp=1., dirichlet=False):
        self.weight = nn.Parameter(tensor(temp))
        self.bias = None
        self.log_softmax = dirichlet

    def forward(self, x):
        if self.log_softmax: x = F.log_softmax(x, dim=-1)
        return x.div(self.weight)


class Vector_Scale(Module):
    "Used to perform Vector Scaling (dirichlet=False) or Diagonal Dirichlet calibration (dirichlet=True)"
    def __init__(self, n_classes=1, dirichlet=False):
        self.weight = nn.Parameter(torch.ones(n_classes))
        self.bias = nn.Parameter(torch.zeros(n_classes))
        self.log_softmax = dirichlet

    def forward(self, x):
        if self.log_softmax: x = F.log_softmax(x, dim=-1)
        return x.mul(self.weight).add(self.bias)


class Matrix_Scale(Module):
    "Used to perform Matrix Scaling (dirichlet=False) or Dirichlet calibration (dirichlet=True)"
    def __init__(self, n_classes=1, dirichlet=False):
        self.ms = nn.Linear(n_classes, n_classes)
        self.ms.weight.data = nn.Parameter(torch.eye(n_classes))
        nn.init.constant_(self.ms.bias.data, 0.)
        self.weight = self.ms.weight
        self.bias = self.ms.bias
        self.log_softmax = dirichlet

    def forward(self, x):
        if self.log_softmax: x = F.log_softmax(x, dim=-1)
        return self.ms(x)


def get_calibrator(calibrator=None, n_classes=1, **kwargs):
    if calibrator is None or not calibrator: return noop
    elif calibrator.lower() == 'temp': return Temp_Scale(dirichlet=False, **kwargs)
    elif calibrator.lower() == 'vector': return Vector_Scale(n_classes=n_classes, dirichlet=False, **kwargs)
    elif calibrator.lower() == 'matrix': return Matrix_Scale(n_classes=n_classes, dirichlet=False, **kwargs)
    elif calibrator.lower() == 'dtemp': return Temp_Scale(dirichlet=True, **kwargs)
    elif calibrator.lower() == 'dvector': return Vector_Scale(n_classes=n_classes, dirichlet=True, **kwargs)
    elif calibrator.lower() == 'dmatrix': return Matrix_Scale(n_classes=n_classes, dirichlet=True, **kwargs)
    else: assert False, f'please, select a correct calibrator instead of {calibrator}'

# Cell
class LogitAdjustmentLayer(Module):
    "Logit Adjustment for imbalanced datasets"
    def __init__(self, class_priors):
        self.class_priors = class_priors
    def forward(self, x):
        return x.add(self.class_priors)

LogitAdjLayer = LogitAdjustmentLayer

# Cell
class PPV(Module):
    def __init__(self, dim=-1):
        self.dim = dim
    def forward(self, x):
        return torch.gt(x, 0).sum(dim=self.dim).float() / x.shape[self.dim]
    def __repr__(self): return f'{self.__class__.__name__}(dim={self.dim})'


class PPAuc(Module):
    def __init__(self, dim=-1):
        self.dim = dim
    def forward(self, x):
        x = F.relu(x).sum(self.dim) / (abs(x).sum(self.dim) + 1e-8)
        return x
    def __repr__(self): return f'{self.__class__.__name__}(dim={self.dim})'


class MaxPPVPool1d(Module):
    "Drop-in replacement for AdaptiveConcatPool1d - multiplies nf by 2"
    def forward(self, x):
        _max = x.max(dim=-1).values
        _ppv = torch.gt(x, 0).sum(dim=-1).float() / x.shape[-1]
        return torch.cat((_max, _ppv), dim=-1).unsqueeze(2)

# Cell
class AdaptiveWeightedAvgPool1d(Module):
    def __init__(self, n_in, seq_len, output_size=1, by_channel=True, n_layers=2, ln=False, dropout=0.5, act=nn.ReLU(), zero_init=False):
        if n_layers == 1:
            act = None
        self.output_size = output_size
        self.conv = nn.Conv1d(n_in, output_size, 1) if not by_channel else None
        layers = nn.ModuleList()
        for i in range(n_layers):
            layers.append(LinLnDrop(seq_len, seq_len, ln=ln, p=dropout, act=act if i < n_layers-1 else None))
        self.layers = layers
        self.softmax = SoftMax(-1)
        if zero_init:
            init_lin_zero(self)

    def forward(self, x):
        gup = x
        if self.conv is not None:
            gup = self.conv(gup)
        for l in self.layers:
            gup = l(gup)
        gup = self.softmax(gup)
        _out = []
        for i in range(self.output_size):
            _out.append(torch.mul(x, gup[:, i][:, np.newaxis]).sum(-1))
        return torch.stack(_out, -1)

# Cell
class GAP1d(Module):
    "Global Adaptive Pooling + Flatten"
    def __init__(self, output_size=1):
        self.gap = nn.AdaptiveAvgPool1d(output_size)
        self.flatten = Flatten()
    def forward(self, x):
        return self.flatten(self.gap(x))


class GACP1d(Module):
    "Global AdaptiveConcatPool + Flatten"
    def __init__(self, output_size=1):
        self.gacp = AdaptiveConcatPool1d(output_size)
        self.flatten = Flatten()
    def forward(self, x):
        return self.flatten(self.gacp(x))


class GAWP1d(Module):
    "Global AdaptiveWeightedAvgPool1d + Flatten"
    def __init__(self, n_in, seq_len, output_size=1, by_channel=True, n_layers=2, ln=False, dropout=0.5, act=nn.ReLU(), zero_init=False):
        self.gacp = AdaptiveWeightedAvgPool1d(n_in, seq_len, output_size=output_size, by_channel=by_channel, n_layers=n_layers,
                                              ln=ln, dropout=dropout, act=act, zero_init=zero_init)
        self.flatten = Flatten()
    def forward(self, x):
        return self.flatten(self.gacp(x))

# Cell
class GlobalWeightedAveragePool1d(Module):
    r""" Global Weighted Average Pooling layer inspired by Building Efficient CNN Architecture for Offline Handwritten Chinese Character Recognition
    https://arxiv.org/pdf/1804.01259.pdf"""
    def __init__(self, n_in, seq_len):
        self.weight = nn.Parameter(torch.ones(1, n_in, seq_len))
        self.bias = nn.Parameter(torch.zeros(1, 1, seq_len))

    def forward(self, x):
        α = F.softmax(torch.sigmoid(x * self.weight + self.bias), dim=-1)
        return (x * α).sum(-1)

GWAP1d = GlobalWeightedAveragePool1d

def gwa_pool_head(n_in, c_out, seq_len, bn=False, fc_dropout=0.):
    return nn.Sequential(GlobalWeightedAveragePool1d(n_in, seq_len), Flatten(), LinBnDrop(n_in, c_out, p=fc_dropout, bn=bn))

# Cell
class AttentionalPool1d(Module):
    """Global Adaptive Pooling layer inspired by Attentional Pooling for Action Recognition https://arxiv.org/abs/1711.01467"""
    def __init__(self, n_in, c_out, bn=False):
        store_attr()
        self.bn = nn.BatchNorm1d(n_in) if bn else None
        self.conv1 = Conv1d(n_in, 1, 1)
        self.conv2 = Conv1d(n_in, c_out, 1)

    def forward(self, x):
        if self.bn is not None: x = self.bn(x)
        return (self.conv1(x) @ self.conv2(x).transpose(1,2)).transpose(1,2)

class GAttP1d(nn.Sequential):
    def __init__(self, n_in, c_out, bn=False):
        super().__init__(AttentionalPool1d(n_in, c_out, bn=bn), Flatten())

def attentional_pool_head(n_in, c_out, seq_len=None, bn=True, **kwargs):
    return nn.Sequential(AttentionalPool1d(n_in, c_out, bn=bn, **kwargs), Flatten())

# Cell
def create_pool_head(n_in, c_out, seq_len=None, concat_pool=False, fc_dropout=0., bn=False, y_range=None, **kwargs):
    if kwargs: print(f'{kwargs}  not being used')
    if concat_pool: n_in*=2
    layers = [GACP1d(1) if concat_pool else GAP1d(1)]
    layers += [LinBnDrop(n_in, c_out, bn=bn, p=fc_dropout)]
    if y_range: layers += [SigmoidRange(*y_range)]
    return nn.Sequential(*layers)

pool_head = create_pool_head
average_pool_head = partial(pool_head, concat_pool=False)
setattr(average_pool_head, "__name__", "average_pool_head")
concat_pool_head = partial(pool_head, concat_pool=True)
setattr(concat_pool_head, "__name__", "concat_pool_head")

# Cell
def max_pool_head(n_in, c_out, seq_len, fc_dropout=0., bn=False, y_range=None, **kwargs):
    if kwargs: print(f'{kwargs}  not being used')
    layers = [nn.MaxPool1d(seq_len, **kwargs), Flatten()]
    layers += [LinBnDrop(n_in, c_out, bn=bn, p=fc_dropout)]
    if y_range: layers += [SigmoidRange(*y_range)]
    return nn.Sequential(*layers)

# Cell
def create_pool_plus_head(*args, lin_ftrs=None, fc_dropout=0., concat_pool=True, bn_final=False, lin_first=False, y_range=None):
    nf = args[0]
    c_out = args[1]
    if concat_pool: nf = nf * 2
    lin_ftrs = [nf, 512, c_out] if lin_ftrs is None else [nf] + lin_ftrs + [c_out]
    ps = L(fc_dropout)
    if len(ps) == 1: ps = [ps[0]/2] * (len(lin_ftrs)-2) + ps
    actns = [nn.ReLU(inplace=True)] * (len(lin_ftrs)-2) + [None]
    pool = AdaptiveConcatPool1d() if concat_pool else nn.AdaptiveAvgPool1d(1)
    layers = [pool, Flatten()]
    if lin_first: layers.append(nn.Dropout(ps.pop(0)))
    for ni,no,p,actn in zip(lin_ftrs[:-1], lin_ftrs[1:], ps, actns):
        layers += LinBnDrop(ni, no, bn=True, p=p, act=actn, lin_first=lin_first)
    if lin_first: layers.append(nn.Linear(lin_ftrs[-2], c_out))
    if bn_final: layers.append(nn.BatchNorm1d(lin_ftrs[-1], momentum=0.01))
    if y_range is not None: layers.append(SigmoidRange(*y_range))
    return nn.Sequential(*layers)

pool_plus_head = create_pool_plus_head

# Cell
def create_conv_head(*args, adaptive_size=None, y_range=None):
    nf = args[0]
    c_out = args[1]
    layers = [nn.AdaptiveAvgPool1d(adaptive_size)] if adaptive_size is not None else []
    for i in range(2):
        if nf > 1:
            layers += [ConvBlock(nf, nf // 2, 1)]
            nf = nf//2
        else: break
    layers += [ConvBlock(nf, c_out, 1), GAP1d(1)]
    if y_range: layers += [SigmoidRange(*y_range)]
    return nn.Sequential(*layers)

conv_head = create_conv_head

# Cell
def create_mlp_head(nf, c_out, seq_len=None, flatten=True, fc_dropout=0., bn=False, y_range=None):
    if flatten: nf *= seq_len
    layers = [Flatten()] if flatten else []
    layers += [LinBnDrop(nf, c_out, bn=bn, p=fc_dropout)]
    if y_range: layers += [SigmoidRange(*y_range)]
    return nn.Sequential(*layers)

mlp_head = create_mlp_head

# Cell
def create_fc_head(nf, c_out, seq_len=None, flatten=True, lin_ftrs=None, y_range=None, fc_dropout=0., bn=False, bn_final=False, act=nn.ReLU(inplace=True)):
    if flatten: nf *= seq_len
    layers = [Flatten()] if flatten else []
    lin_ftrs = [nf, 512, c_out] if lin_ftrs is None else [nf] + lin_ftrs + [c_out]
    if not is_listy(fc_dropout): fc_dropout = [fc_dropout]*(len(lin_ftrs) - 1)
    actns = [act for _ in range(len(lin_ftrs) - 2)] + [None]
    layers += [LinBnDrop(lin_ftrs[i], lin_ftrs[i+1], bn=bn and (i!=len(actns)-1 or bn_final), p=p, act=a) for i,(p,a) in enumerate(zip(fc_dropout+[0.], actns))]
    if y_range is not None: layers.append(SigmoidRange(*y_range))
    return nn.Sequential(*layers)

fc_head = create_fc_head

# Cell
def create_rnn_head(*args, fc_dropout=0., bn=False, y_range=None):
    nf = args[0]
    c_out = args[1]
    layers = [LastStep()]
    layers += [LinBnDrop(nf, c_out, bn=bn, p=fc_dropout)]
    if y_range: layers += [SigmoidRange(*y_range)]
    return nn.Sequential(*layers)

rnn_head = create_rnn_head

# Cell
class create_conv_lin_3d_head(nn.Sequential):
    "Module to create a 3d output head"

    def __init__(self, n_in, n_out, seq_len, d=None, conv_first=True, conv_bn=True, lin_first=False, lin_bn=True, act=None, fc_dropout=0., **kwargs):

        d = ifnone(d, 1)
        conv = [BatchNorm(n_in, ndim=1)] if conv_bn else []
        conv.append(Conv1d(n_in, n_out, 1, padding=0, bias=not conv_bn, **kwargs))

        l = [Transpose(-1, -2), BatchNorm(d if lin_first else seq_len, ndim=1), Transpose(-1, -2)] if lin_bn else []
        if fc_dropout != 0: l.append(nn.Dropout(fc_dropout))

        lin = [nn.Linear(seq_len, d, bias=not lin_bn)]
        if act is not None: lin.append(act)

        lin_layers = lin+l if lin_first else l+lin
        layers = conv + lin_layers if conv_first else lin_layers + conv

        if d == 1: layers += [Squeeze(-1)]

        super().__init__(*layers)

conv_lin_3d_head = create_conv_lin_3d_head

# Cell
class create_lin_3d_head(nn.Sequential):
    "Module to create a 3d output head with linear layers"

    def __init__(self, n_in, n_out, seq_len, d=None, lin_first=False, bn=True, act=None, fc_dropout=0.):

        layers = [Flatten()]
        _n_out = n_out * d if d is not None else n_out
        layers += LinBnDrop(n_in * seq_len, _n_out, bn=bn, p=fc_dropout, act=act, lin_first=lin_first)
        if d is not None:
            layers += [Reshape(n_out, d)]

        super().__init__(*layers)

lin_3d_head = create_lin_3d_head

# Cell
def universal_pool_head(n_in, c_out, seq_len, output_size=1, by_channel=True, pool_n_layers=2, pool_ln=False, pool_dropout=0.5, pool_act=nn.ReLU(),
                   zero_init=True, bn=False, fc_dropout=0.):
    layers = [AdaptiveWeightedAvgPool1d(n_in, seq_len, output_size=output_size, by_channel=by_channel, n_layers=pool_n_layers, ln=pool_ln,
                                        dropout=pool_dropout, act=pool_act), Flatten(), LinBnDrop(n_in * output_size, c_out, p=fc_dropout, bn=bn)]
    return nn.Sequential(*layers)

# Cell
heads = [mlp_head, fc_head, average_pool_head, max_pool_head, concat_pool_head, pool_plus_head, conv_head, rnn_head, conv_lin_3d_head, lin_3d_head,
         attentional_pool_head, universal_pool_head, gwa_pool_head]

# Cell
class SqueezeExciteBlock(Module):
    def __init__(self, ni, reduction=16):
        self.avg_pool = GAP1d(1)
        self.fc = nn.Sequential(nn.Linear(ni, ni // reduction, bias=False), nn.ReLU(),  nn.Linear(ni // reduction, ni, bias=False), nn.Sigmoid())

    def forward(self, x):
        y = self.avg_pool(x)
        y = self.fc(y).unsqueeze(2)
        return x * y.expand_as(x)

# Cell
class GaussianNoise(Module):
    """Gaussian noise regularizer.

    Args:
        sigma (float, optional): relative standard deviation used to generate the
            noise. Relative means that it will be multiplied by the magnitude of
            the value your are adding the noise to. This means that sigma can be
            the same regardless of the scale of the vector.
        is_relative_detach (bool, optional): whether to detach the variable before
            computing the scale of the noise. If `False` then the scale of the noise
            won't be seen as a constant but something to optimize: this will bias the
            network to generate vectors with smaller values.
    """

    def __init__(self, sigma=0.1, is_relative_detach=True):
        self.sigma, self.is_relative_detach = sigma, is_relative_detach

    def forward(self, x):
        if self.training and self.sigma not in [0, None]:
            scale = self.sigma * (x.detach() if self.is_relative_detach else x)
            sampled_noise = torch.empty(x.size()).normal_().to(device) * scale
            x = x + sampled_noise
        return x

# Cell
def gambler_loss(reward=2):
    def _gambler_loss(model_output, targets):
        outputs = torch.nn.functional.softmax(model_output, dim=1)
        outputs, reservation = outputs[:, :-1], outputs[:, -1]
        gain = torch.gather(outputs, dim=1, index=targets.unsqueeze(1)).squeeze()
        doubling_rate = (gain + reservation / reward).log()
        return - doubling_rate.mean()
    return _gambler_loss

# Cell
def CrossEntropyLossOneHot(output, target, **kwargs):
    if target.ndim == 2: _, target = target.max(dim=1)
    return nn.CrossEntropyLoss(**kwargs)(output, target)

# Cell
def ttest_bin_loss(output, target):
    output = nn.Softmax(dim=-1)(output[:, 1])
    return ttest_tensor(output[target == 0], output[target == 1])

def ttest_reg_loss(output, target):
    return ttest_tensor(output[target <= 0], output[target > 0])

# Cell
class CenterLoss(Module):
    r"""
    Code in Pytorch has been slightly modified from: https://github.com/KaiyangZhou/pytorch-center-loss/blob/master/center_loss.py
    Based on paper: Wen et al. A Discriminative Feature Learning Approach for Deep Face Recognition. ECCV 2016.

    Args:
        c_out (int): number of classes.
        logits_dim (int): dim 1 of the logits. By default same as c_out (for one hot encoded logits)

    """
    def __init__(self, c_out, logits_dim=None):
        logits_dim = ifnone(logits_dim, c_out)
        self.c_out, self.logits_dim = c_out, logits_dim
        self.centers = nn.Parameter(torch.randn(c_out, logits_dim).to(device=default_device()))
        self.classes = torch.arange(c_out).long().to(device=default_device())

    def forward(self, x, labels):
        """
        Args:
            x: feature matrix with shape (batch_size, logits_dim).
            labels: ground truth labels with shape (batch_size).
        """
        bs = x.shape[0]
        distmat = torch.pow(x, 2).sum(dim=1, keepdim=True).expand(bs, self.c_out) + \
                  torch.pow(self.centers, 2).sum(dim=1, keepdim=True).expand(self.c_out, bs).T
        distmat = torch.addmm(distmat, x, self.centers.T, beta=1, alpha=-2)

        labels = labels.unsqueeze(1).expand(bs, self.c_out)
        mask = labels.eq(self.classes.expand(bs, self.c_out))

        dist = distmat * mask.float()
        loss = dist.clamp(min=1e-12, max=1e+12).sum() / bs

        return loss


class CenterPlusLoss(Module):

    def __init__(self, loss, c_out, λ=1e-2, logits_dim=None):
        self.loss, self.c_out, self.λ = loss, c_out, λ
        self.centerloss = CenterLoss(c_out, logits_dim)

    def forward(self, x, labels):
        return self.loss(x, labels) + self.λ * self.centerloss(x, labels)
    def __repr__(self): return f"CenterPlusLoss(loss={self.loss}, c_out={self.c_out}, λ={self.λ})"

# Cell
class FocalLoss(Module):

    def __init__(self, gamma=0, eps=1e-7):
        self.gamma, self.eps, self.ce = gamma, eps, CrossEntropyLossFlat()

    def forward(self, input, target):
        logp = self.ce(input, target)
        p = torch.exp(-logp)
        loss = (1 - p) ** self.gamma * logp
        return loss.mean()

# Cell
class TweedieLoss(Module):
    def __init__(self, p=1.5, eps=1e-10):
        """
        Tweedie loss as calculated in LightGBM
        Args:
            p: tweedie variance power (1 < p < 2)
            eps: small number to avoid log(zero).
        """
        assert p > 1 and p < 2, "make sure 1 < p < 2"
        self.p, self.eps = p, eps

    def forward(self, inp, targ):
        inp = inp.flatten()
        targ = targ.flatten()
        torch.clamp_min_(inp, self.eps)
        a = targ * torch.exp((1 - self.p) * torch.log(inp)) / (1 - self.p)
        b = torch.exp((2 - self.p) * torch.log(inp)) / (2 - self.p)
        loss = -a + b
        return loss.mean()