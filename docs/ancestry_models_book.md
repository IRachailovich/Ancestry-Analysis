# Mathematical Models for Ancestry Analysis

Conditional random fields, RFMix, string kernels, qpGraph, and qpAdm

Author: Codex  
Date: 2026-05-06

## Preface

This manuscript is a mathematical introduction to five models and model families that appear in ancestry analysis:

1. Conditional random fields (CRFs).
2. RFMix, a discriminative local-ancestry model built around random forests and a conditional random field.
3. String kernels for representing haplotypes, genotypes, and sequence-like ancestry data.
4. qpGraph, a graph-based model for fitting population splits, drift, and admixture.
5. qpAdm, a related framework for testing whether a target population can be modeled as a mixture of proposed sources.

The goal is not only to state formulas, but to derive them. I assume the reader knows basic algebra, but I do not assume they already know probabilistic graphical models, kernel machines, local ancestry inference, or f-statistics. Some biological details are necessarily simplified so the mathematics is visible.

## Sources and Reading Map

Primary and technical sources used:

- Lafferty, McCallum, and Pereira, "Conditional Random Fields: Probabilistic Models for Segmenting and Labeling Sequence Data" (2001): https://repository.upenn.edu/entities/publication/c8b4b2a3-cc00-4e08-851f-0caa55b8fefe
- Sutton and McCallum, "An Introduction to Conditional Random Fields" (2010): https://arxiv.org/abs/1011.4088
- Maples, Gravel, Kenny, and Bustamante, "RFMix: A Discriminative Modeling Approach for Rapid and Robust Local-Ancestry Inference" (2013): https://www.cell.com/ajhg/fulltext/S0002-9297(13)00289-9
- RFMix source repository and usage notes: https://github.com/slowkoni/rfmix
- Lodhi et al., "Text Classification using String Kernels" (2002): https://www.jmlr.org/papers/v2/lodhi02a.html
- Leslie, Eskin, and Noble, "The spectrum kernel: a string kernel for SVM protein classification" (2002): https://psb.stanford.edu/psb-online/proceedings/psb02/leslie.pdf
- Patterson et al., "Ancient Admixture in Human History" (2012), introducing ADMIXTOOLS and f-statistic machinery: https://pmc.ncbi.nlm.nih.gov/articles/PMC3522152/
- ADMIXTOOLS 2 documentation for qpGraph: https://uqrmaie1.github.io/admixtools/articles/qpgraph.html
- ADMIXTOOLS 2 documentation for qpAdm: https://uqrmaie1.github.io/admixtools/articles/qpadm.html
- Harney et al., "Assessing the performance of qpAdm" (2021): https://pmc.ncbi.nlm.nih.gov/articles/PMC8248411/
- ADMIXTOOLS 2 package paper: https://academic.oup.com/genetics/article/216/4/913/6065872

The citations above are enough to reconstruct the intellectual lineage: CRFs give a conditional sequence model; RFMix adapts that structure to local ancestry; string kernels provide nonparametric similarity measures for sequence-like genetic data; qpGraph and qpAdm use f-statistics to summarize allele-frequency covariance patterns caused by drift and admixture.

## Common Mathematical Foundations

Before entering the five chapters, we need a common notation. Genetic ancestry methods often differ in surface appearance, but many of them reduce to the same small set of mathematical objects:

- observed data,
- hidden ancestry labels or latent graph histories,
- a probability model or moment model,
- an objective function,
- an inference algorithm,
- an uncertainty estimate.

### Random Variables and Observations

A random variable is a quantity whose value is unknown before observation. If \(X\) is discrete and can take values in a set \(\mathcal X\), a probability mass function assigns each possible value \(x\) a number

\[
P(X=x)\ge 0
\]

such that

\[
\sum_{x\in\mathcal X} P(X=x)=1.
\]

The first condition says probabilities cannot be negative. The second says that one of the possible outcomes must occur.

For a pair of random variables \(X\) and \(Y\), the joint probability is

\[
P(X=x,Y=y).
\]

The marginal probability of \(X=x\) is obtained by summing over all possible values of \(Y\):

\[
P(X=x)=\sum_{y\in\mathcal Y}P(X=x,Y=y).
\]

The conditional probability of \(Y=y\) given \(X=x\) is defined by

\[
P(Y=y\mid X=x)=\frac{P(X=x,Y=y)}{P(X=x)}
\]

whenever \(P(X=x)>0\). Rearranging gives the product rule:

\[
P(X=x,Y=y)=P(Y=y\mid X=x)P(X=x).
\]

This product rule is the seed from which graphical models grow. A model becomes useful when it factors a large joint probability into smaller conditional pieces.

### Genotypes, Haplotypes, and Ancestry Labels

At a biallelic marker \(i\), a haploid allele can be represented as

\[
x_i\in\{0,1\},
\]

where \(0\) means reference allele and \(1\) means alternate allele. A diploid genotype can be represented as

\[
g_i=x_i^{(1)}+x_i^{(2)}\in\{0,1,2\}.
\]

A haplotype across \(L\) markers is a sequence

\[
x=(x_1,x_2,\ldots,x_L).
\]

For local ancestry, each chromosomal position also has a hidden ancestry label. If there are \(K\) possible ancestral populations, then

\[
z_i\in\{1,2,\ldots,K\}.
\]

For a diploid individual with phased haplotypes, there are two ancestry-label sequences,

\[
z^{(1)}=(z_1^{(1)},\ldots,z_L^{(1)}),\qquad
z^{(2)}=(z_1^{(2)},\ldots,z_L^{(2)}).
\]

The central local-ancestry problem is:

\[
\text{infer } z \text{ from observed genetic data } x.
\]

That sentence hides a large difficulty. Recombination makes ancestry labels spatially correlated, allele frequencies make observations ancestry-informative but noisy, and reference panels are finite and imperfect. RFMix addresses this by combining local classifiers with a sequence model.

### Likelihood and Maximum Likelihood

Suppose a model has parameter vector \(\theta\), and the observed data are \(D\). The likelihood is

\[
L(\theta;D)=P_\theta(D).
\]

It is the probability of the observed data as a function of the unknown parameter. Since products of many probabilities are numerically small, we usually use the log-likelihood:

\[
\ell(\theta;D)=\log L(\theta;D).
\]

The logarithm is useful because it turns products into sums:

\[
\log\prod_{i=1}^n a_i=\sum_{i=1}^n\log a_i.
\]

Maximum likelihood estimation chooses

\[
\hat\theta=\arg\max_\theta \ell(\theta;D).
\]

In discriminative sequence models such as CRFs, the model does not try to describe the full probability \(P(x,z)\). Instead it models

\[
P(z\mid x).
\]

That distinction matters. A generative model must explain how genetic observations are produced. A discriminative model can directly focus on labeling accuracy: given the observed haplotype or genotype context, which ancestry label sequence is most plausible?

### Expectations

For a discrete random variable \(X\) and a function \(h(X)\), the expectation is

\[
\mathbb E[h(X)] = \sum_{x\in\mathcal X} h(x)P(X=x).
\]

This is a weighted average. If \(h(x)\) is large where \(P(X=x)\) is large, the expectation is large.

Expectations appear constantly in model fitting. For example, the gradient of a CRF log-likelihood is "observed feature counts minus expected feature counts." This is not a slogan; it follows by differentiating the log partition function. We will derive it in Chapter 1.

### Covariance

For random variables \(X\) and \(Y\), covariance is

\[
\operatorname{Cov}(X,Y)
=\mathbb E[(X-\mathbb E[X])(Y-\mathbb E[Y])].
\]

Expanding:

\[
\begin{aligned}
\operatorname{Cov}(X,Y)
&=\mathbb E[XY-X\mathbb E[Y]-Y\mathbb E[X]+\mathbb E[X]\mathbb E[Y]]\\
&=\mathbb E[XY]-\mathbb E[X]\mathbb E[Y]-\mathbb E[Y]\mathbb E[X]+\mathbb E[X]\mathbb E[Y]\\
&=\mathbb E[XY]-\mathbb E[X]\mathbb E[Y].
\end{aligned}
\]

The f-statistics used by qpGraph and qpAdm are functions of allele-frequency differences. They can be understood as covariance-like summaries of shared drift.

### Positive Semidefinite Kernels

A kernel is a function

\[
K(x,y)
\]

that measures similarity between two objects. A kernel is positive semidefinite if, for any finite set \(x_1,\ldots,x_n\) and real coefficients \(c_1,\ldots,c_n\),

\[
\sum_{i=1}^n\sum_{j=1}^n c_i c_j K(x_i,x_j)\ge 0.
\]

The reason this condition matters is that it guarantees the existence of a feature map \(\phi\) into an inner-product space such that

\[
K(x,y)=\langle \phi(x),\phi(y)\rangle.
\]

String kernels compare strings by counting shared substrings, shared subsequences, or approximate matches. They become powerful in ancestry analysis because haplotypes are naturally string-like objects.

### Least Squares and Weighted Least Squares

Suppose observed statistics are collected in a vector \(s\in\mathbb R^m\), and a model predicts \(\mu(\theta)\in\mathbb R^m\). The residual is

\[
r(\theta)=s-\mu(\theta).
\]

Ordinary least squares minimizes

\[
Q(\theta)=r(\theta)^T r(\theta).
\]

If the statistics have different variances and covariances, we use a covariance matrix \(\Sigma\). Weighted least squares minimizes

\[
Q(\theta)=r(\theta)^T\Sigma^{-1}r(\theta).
\]

This form appears in qpGraph: observed f-statistics are compared to f-statistics predicted by an admixture graph. The inverse covariance matrix gives less weight to noisy directions and more weight to precise directions.

# Chapter 1. Conditional Random Fields

## 1.1 Big Picture

A conditional random field is a probabilistic model for structured prediction. In ordinary classification, the output is a single label:

\[
x\mapsto y.
\]

In structured prediction, the output is a collection of labels:

\[
x\mapsto y=(y_1,\ldots,y_L).
\]

In ancestry analysis, a natural example is local ancestry:

\[
\text{observed haplotype markers}\mapsto\text{ancestry label at each marker}.
\]

The labels are not independent. If marker \(i\) has African ancestry on a chromosome, marker \(i+1\) is also likely to have African ancestry unless a recombination event occurred between the two markers. A model that labels each marker independently throws away this spatial structure.

CRFs solve this problem by modeling the conditional distribution

\[
P(y\mid x)
\]

while allowing neighboring labels to interact.

## 1.2 The Problem CRFs Tackle

Suppose we observe an input sequence

\[
x=(x_1,\ldots,x_L),
\]

and want to infer a label sequence

\[
y=(y_1,\ldots,y_L),\qquad y_i\in\mathcal Y.
\]

A naive independent classifier would use

\[
P(y\mid x)=\prod_{i=1}^L P(y_i\mid x).
\]

This is simple, but it says

\[
y_i \perp y_j \mid x
\]

for all \(i\ne j\). In words: after seeing the input, all labels are independent. That is rarely true for sequence data.

A hidden Markov model instead uses a generative factorization:

\[
P(x,y)=P(y_1)P(x_1\mid y_1)\prod_{i=2}^L P(y_i\mid y_{i-1})P(x_i\mid y_i).
\]

By Bayes' rule,

\[
P(y\mid x)=\frac{P(x,y)}{P(x)}.
\]

The HMM captures label dependence, but it imposes a particular model for generating observations. In many applications, including ancestry labeling with rich windows of markers, we want to use arbitrary features of \(x\) without specifying a full probability model for \(x\).

CRFs combine the strengths:

- they model \(P(y\mid x)\) directly;
- they allow dependencies among labels;
- they support arbitrary feature functions of the observed input.

## 1.3 From Logistic Regression to CRFs

Start with multiclass logistic regression. Let \(y\in\{1,\ldots,K\}\), and let \(f_k(x)\) be a score for class \(k\). A common linear score is

\[
s_k(x)=w_k^T x.
\]

Scores are arbitrary real numbers. To turn them into probabilities, exponentiate them:

\[
\exp(s_k(x))>0.
\]

Then normalize:

\[
P(y=k\mid x)=\frac{\exp(s_k(x))}{\sum_{\ell=1}^K \exp(s_\ell(x))}.
\]

The denominator is needed because the probabilities must sum to one:

\[
\sum_{k=1}^K P(y=k\mid x)
=\sum_{k=1}^K\frac{\exp(s_k(x))}{\sum_{\ell=1}^K \exp(s_\ell(x))}
=\frac{\sum_{k=1}^K\exp(s_k(x))}{\sum_{\ell=1}^K\exp(s_\ell(x))}
=1.
\]

Now replace a single label \(y\) with a sequence \(y=(y_1,\ldots,y_L)\). We can assign a score to the whole sequence:

\[
S(y,x)=\sum_{j=1}^p \theta_j F_j(y,x),
\]

where each \(F_j\) is a feature of the complete label sequence and the observed input. The conditional probability becomes

\[
P_\theta(y\mid x)=\frac{\exp(S(y,x))}{Z_\theta(x)}
\]

where

\[
Z_\theta(x)=\sum_{y'\in\mathcal Y^L}\exp(S(y',x)).
\]

The denominator \(Z_\theta(x)\) is called the partition function. It depends on \(x\), because this is a conditional model.

Again, verify normalization:

\[
\sum_{y\in\mathcal Y^L}P_\theta(y\mid x)
=\sum_y\frac{\exp(S(y,x))}{Z_\theta(x)}
=\frac{\sum_y\exp(S(y,x))}{Z_\theta(x)}
=1.
\]

This is the general log-linear conditional random field form.

## 1.4 Linear-Chain CRF Factorization

For a sequence, the most common CRF is a linear-chain CRF. It uses local features that depend on adjacent labels:

\[
F_j(y,x)=\sum_{i=1}^L f_j(y_{i-1},y_i,x,i).
\]

Here \(f_j\) is a local feature function. The previous label \(y_{i-1}\) allows transition features. For \(i=1\), one usually introduces a special start state \(y_0=\text{START}\).

The sequence score is

\[
S(y,x)=\sum_{j=1}^p \theta_j\sum_{i=1}^L f_j(y_{i-1},y_i,x,i).
\]

Switching the order of summation:

\[
S(y,x)=\sum_{i=1}^L\sum_{j=1}^p \theta_j f_j(y_{i-1},y_i,x,i).
\]

Define the local potential

\[
\psi_i(a,b,x)=\exp\left(\sum_{j=1}^p\theta_j f_j(a,b,x,i)\right).
\]

Then

\[
\exp(S(y,x))
=\exp\left(\sum_{i=1}^L\sum_j\theta_j f_j(y_{i-1},y_i,x,i)\right).
\]

Using \(\exp(u+v)=\exp(u)\exp(v)\), this becomes

\[
\exp(S(y,x))
=\prod_{i=1}^L
\exp\left(\sum_j\theta_j f_j(y_{i-1},y_i,x,i)\right)
=\prod_{i=1}^L\psi_i(y_{i-1},y_i,x).
\]

So the model can be written as

\[
P_\theta(y\mid x)
=\frac{1}{Z_\theta(x)}
\prod_{i=1}^L\psi_i(y_{i-1},y_i,x).
\]

This factorization is the mathematical reason inference is possible. Naively summing over all label sequences costs \(K^L\), which is impossible for large \(L\). The linear-chain structure lets us use dynamic programming.

## 1.5 The Partition Function by Forward Recursion

The partition function is

\[
Z_\theta(x)=\sum_{y_1}\cdots\sum_{y_L}\prod_{i=1}^L\psi_i(y_{i-1},y_i,x).
\]

Let

\[
\alpha_i(b)
\]

be the total unnormalized weight of all partial label sequences ending in state \(b\) at position \(i\):

\[
\alpha_i(b)
=\sum_{y_1,\ldots,y_{i-1}}
\prod_{t=1}^i\psi_t(y_{t-1},y_t,x)
\quad\text{with } y_i=b.
\]

For \(i=1\),

\[
\alpha_1(b)=\psi_1(\text{START},b,x).
\]

For \(i>1\), split the partial sequence according to the previous state \(a=y_{i-1}\):

\[
\alpha_i(b)
=\sum_{a\in\mathcal Y}
\left[
\sum_{y_1,\ldots,y_{i-2}}
\prod_{t=1}^{i-1}\psi_t(y_{t-1},y_t,x)
\right]\psi_i(a,b,x).
\]

The bracketed term is \(\alpha_{i-1}(a)\). Therefore

\[
\alpha_i(b)=\sum_{a\in\mathcal Y}\alpha_{i-1}(a)\psi_i(a,b,x).
\]

Finally, sum over the last state:

\[
Z_\theta(x)=\sum_{b\in\mathcal Y}\alpha_L(b).
\]

The cost is \(O(LK^2)\), because for each of \(L\) positions we compute \(K\) states, each requiring a sum over \(K\) previous states.

## 1.6 Backward Recursion

The backward value \(\beta_i(a)\) is the total unnormalized weight of the suffix from \(i+1\) to \(L\), given that \(y_i=a\):

\[
\beta_i(a)=
\sum_{y_{i+1},\ldots,y_L}
\prod_{t=i+1}^L\psi_t(y_{t-1},y_t,x)
\quad\text{with } y_i=a.
\]

At the end,

\[
\beta_L(a)=1
\]

because an empty product equals one. For \(i<L\), split by the next state \(b=y_{i+1}\):

\[
\beta_i(a)=\sum_{b\in\mathcal Y}\psi_{i+1}(a,b,x)\beta_{i+1}(b).
\]

Forward and backward recursions allow marginal probabilities.

## 1.7 Marginal Probability of a Label

We want

\[
P(y_i=b\mid x).
\]

By definition,

\[
P(y_i=b\mid x)=\sum_{y:y_i=b}P(y\mid x).
\]

Substitute the CRF probability:

\[
P(y_i=b\mid x)
=\frac{1}{Z(x)}
\sum_{y:y_i=b}\prod_{t=1}^L\psi_t(y_{t-1},y_t,x).
\]

Every sequence with \(y_i=b\) can be decomposed into a prefix ending at \(b\) and a suffix beginning at \(b\). Therefore the sum factorizes:

\[
\sum_{y:y_i=b}\prod_{t=1}^L\psi_t
=\alpha_i(b)\beta_i(b).
\]

Thus

\[
P(y_i=b\mid x)=\frac{\alpha_i(b)\beta_i(b)}{Z(x)}.
\]

Similarly, the pairwise marginal for adjacent labels is

\[
P(y_{i-1}=a,y_i=b\mid x)
=\frac{\alpha_{i-1}(a)\psi_i(a,b,x)\beta_i(b)}{Z(x)}.
\]

These marginals are needed for training.

## 1.8 Conditional Log-Likelihood

Suppose we have \(N\) training examples:

\[
\{(x^{(n)},y^{(n)})\}_{n=1}^N.
\]

The conditional likelihood is

\[
L(\theta)=\prod_{n=1}^N P_\theta(y^{(n)}\mid x^{(n)}).
\]

The log-likelihood is

\[
\ell(\theta)=\sum_{n=1}^N\log P_\theta(y^{(n)}\mid x^{(n)}).
\]

For one example,

\[
\log P_\theta(y\mid x)
=\log\frac{\exp(S(y,x))}{Z_\theta(x)}
=S(y,x)-\log Z_\theta(x).
\]

Therefore

\[
\ell(\theta)=
\sum_{n=1}^N
\left[
S(y^{(n)},x^{(n)})-\log Z_\theta(x^{(n)})
\right].
\]

Substitute

\[
S(y,x)=\sum_j\theta_jF_j(y,x):
\]

\[
\ell(\theta)=
\sum_{n=1}^N
\left[
\sum_j\theta_jF_j(y^{(n)},x^{(n)})
-\log Z_\theta(x^{(n)})
\right].
\]

## 1.9 Deriving the Gradient

Differentiate with respect to parameter \(\theta_k\):

\[
\frac{\partial\ell}{\partial\theta_k}
=\sum_{n=1}^N
\left[
F_k(y^{(n)},x^{(n)})
-\frac{\partial}{\partial\theta_k}\log Z_\theta(x^{(n)})
\right].
\]

Now derive the partition-function term. For one \(x\),

\[
Z_\theta(x)=\sum_{y'}\exp\left(\sum_j\theta_jF_j(y',x)\right).
\]

By the chain rule,

\[
\frac{\partial Z_\theta(x)}{\partial\theta_k}
=\sum_{y'}
\exp\left(\sum_j\theta_jF_j(y',x)\right)
F_k(y',x).
\]

Because

\[
\frac{\partial}{\partial\theta_k}\log Z_\theta(x)
=\frac{1}{Z_\theta(x)}\frac{\partial Z_\theta(x)}{\partial\theta_k},
\]

we get

\[
\frac{\partial}{\partial\theta_k}\log Z_\theta(x)
=
\sum_{y'}
\frac{\exp(S(y',x))}{Z_\theta(x)}
F_k(y',x).
\]

But

\[
\frac{\exp(S(y',x))}{Z_\theta(x)}
=P_\theta(y'\mid x).
\]

So

\[
\frac{\partial}{\partial\theta_k}\log Z_\theta(x)
=\sum_{y'}P_\theta(y'\mid x)F_k(y',x)
=\mathbb E_\theta[F_k(Y,x)\mid x].
\]

Therefore

\[
\frac{\partial\ell}{\partial\theta_k}
=\sum_{n=1}^N
\left[
F_k(y^{(n)},x^{(n)})
-\mathbb E_\theta[F_k(Y,x^{(n)})\mid x^{(n)}]
\right].
\]

This is the exact "observed minus expected" result.

## 1.10 Convexity of Negative Log-Likelihood

For a single example, the negative log-likelihood is

\[
\mathcal L(\theta)=\log Z_\theta(x)-\sum_j\theta_jF_j(y,x).
\]

The second term is linear in \(\theta\), so its second derivative is zero. Convexity depends on \(\log Z_\theta(x)\).

Compute the second derivative:

\[
\frac{\partial^2}{\partial\theta_j\partial\theta_k}\log Z_\theta(x)
=\frac{\partial}{\partial\theta_j}\mathbb E_\theta[F_k(Y,x)\mid x].
\]

Let \(P_\theta(y\mid x)=p_y\). Then

\[
\mathbb E[F_k]=\sum_y p_yF_k(y,x).
\]

Differentiate:

\[
\frac{\partial}{\partial\theta_j}\mathbb E[F_k]
=\sum_y F_k(y,x)\frac{\partial p_y}{\partial\theta_j}.
\]

Now

\[
p_y=\frac{\exp(S_y)}{Z}.
\]

Differentiate:

\[
\frac{\partial p_y}{\partial\theta_j}
=\frac{\exp(S_y)F_j(y,x)Z-\exp(S_y)\frac{\partial Z}{\partial\theta_j}}{Z^2}.
\]

Divide numerator terms:

\[
\frac{\partial p_y}{\partial\theta_j}
=p_yF_j(y,x)-p_y\frac{1}{Z}\frac{\partial Z}{\partial\theta_j}.
\]

But

\[
\frac{1}{Z}\frac{\partial Z}{\partial\theta_j}=\mathbb E[F_j].
\]

Thus

\[
\frac{\partial p_y}{\partial\theta_j}
=p_y(F_j(y,x)-\mathbb E[F_j]).
\]

Therefore

\[
\frac{\partial^2}{\partial\theta_j\partial\theta_k}\log Z
=\sum_y p_yF_k(y,x)(F_j(y,x)-\mathbb E[F_j]).
\]

Expanding:

\[
=\sum_y p_yF_j(y,x)F_k(y,x)-\mathbb E[F_j]\sum_y p_yF_k(y,x).
\]

Since

\[
\sum_y p_yF_k(y,x)=\mathbb E[F_k],
\]

we get

\[
\frac{\partial^2}{\partial\theta_j\partial\theta_k}\log Z
=\mathbb E[F_jF_k]-\mathbb E[F_j]\mathbb E[F_k]
=\operatorname{Cov}(F_j,F_k).
\]

The Hessian matrix is a covariance matrix. For any vector \(a\),

\[
a^T \operatorname{Cov}(F)a
=\operatorname{Var}(a^TF)\ge 0.
\]

So the Hessian is positive semidefinite, and \(\log Z\) is convex. Therefore the negative log-likelihood is convex for a linear-chain CRF with fixed features. This is one reason CRFs are attractive: training avoids many bad local optima typical of nonconvex models.

## 1.11 Regularization

If the feature set is large, parameters can overfit. Add an \(L_2\) penalty:

\[
\ell_{\text{reg}}(\theta)=\ell(\theta)-\frac{1}{2\sigma^2}\sum_j\theta_j^2.
\]

Differentiate:

\[
\frac{\partial\ell_{\text{reg}}}{\partial\theta_k}
=\frac{\partial\ell}{\partial\theta_k}-\frac{\theta_k}{\sigma^2}.
\]

The penalty corresponds to a Gaussian prior

\[
\theta_j\sim N(0,\sigma^2),
\]

because the log density of a zero-mean Gaussian contains

\[
-\frac{\theta_j^2}{2\sigma^2}
\]

up to constants.

## 1.12 Decoding: The Viterbi Algorithm

Often we want the most likely label sequence:

\[
\hat y=\arg\max_yP(y\mid x).
\]

Since \(Z(x)\) is constant with respect to \(y\),

\[
\hat y=\arg\max_y\prod_{i=1}^L\psi_i(y_{i-1},y_i,x).
\]

Products can underflow, so take logs:

\[
\hat y=\arg\max_y\sum_{i=1}^L\log\psi_i(y_{i-1},y_i,x).
\]

Define

\[
\delta_i(b)=\max_{y_1,\ldots,y_{i-1}}
\sum_{t=1}^i\log\psi_t(y_{t-1},y_t,x)
\quad\text{with }y_i=b.
\]

For \(i=1\),

\[
\delta_1(b)=\log\psi_1(\text{START},b,x).
\]

For \(i>1\),

\[
\delta_i(b)=\max_{a\in\mathcal Y}\left[\delta_{i-1}(a)+\log\psi_i(a,b,x)\right].
\]

Store the maximizing previous state:

\[
\operatorname{back}_i(b)=
\arg\max_{a\in\mathcal Y}\left[\delta_{i-1}(a)+\log\psi_i(a,b,x)\right].
\]

At the end,

\[
\hat y_L=\arg\max_b\delta_L(b),
\]

and then backtrack:

\[
\hat y_{i-1}=\operatorname{back}_i(\hat y_i).
\]

## 1.13 Why CRFs Matter for Ancestry

For ancestry analysis, CRFs address the following challenges:

- Ancestry along a chromosome is spatially correlated.
- Marker-level evidence is noisy and unevenly distributed.
- Nearby labels should change only when recombination makes a switch plausible.
- Rich observed features can be used without modeling the full genotype distribution.

RFMix is a direct example: it uses discriminative local evidence from random forests and then places that evidence inside a CRF-like structure to enforce ancestry continuity.

# Chapter 2. RFMix

## 2.1 Big Picture

RFMix is a model for local ancestry inference. Given an admixed individual and reference panels from ancestral populations, the goal is to assign ancestry labels along the genome. If a chromosome is a mosaic of ancestry segments, RFMix tries to infer where those segments begin and end.

The model is discriminative. It does not primarily ask:

\[
\text{How did the entire observed genome arise under a full generative model?}
\]

Instead it asks:

\[
\text{Given observed genetic markers and references, which ancestry label is most plausible at each genomic region?}
\]

The original RFMix paper combines two ideas:

- a random forest classifier to produce local ancestry evidence from windows of markers;
- a conditional random field to smooth and connect those local decisions along the chromosome.

## 2.2 The Local Ancestry Problem

Let \(i=1,\ldots,L\) index genomic positions or windows. Let \(x_i\) be the observed genetic data near position \(i\). Let

\[
z_i\in\{1,\ldots,K\}
\]

be the unknown ancestry. The inference target is

\[
z=(z_1,\ldots,z_L).
\]

A perfect local ancestry model would use:

- allele-frequency differences between ancestral populations;
- haplotype structure;
- recombination distances;
- reference-panel information;
- the expected number of generations since admixture;
- the possibility of phasing error or genotype uncertainty.

RFMix makes this feasible by separating the problem:

1. produce local ancestry probabilities from a classifier;
2. combine them with transition probabilities across neighboring windows.

## 2.3 Random Forests as Local Classifiers

A decision tree recursively partitions feature space. At a node, a split has the form

\[
x_j\le c
\]

or, for categorical data,

\[
x_j\in A.
\]

For ancestry classification, features can encode alleles or haplotypes in a window. The training data come from reference haplotypes with known population labels.

At a node containing training examples \(S\), let \(n_k\) be the number of examples from class \(k\), and let

\[
\hat p_k=\frac{n_k}{|S|}.
\]

One common impurity measure is Gini impurity:

\[
G(S)=1-\sum_{k=1}^K\hat p_k^2.
\]

Why this formula? If we randomly draw one example from the node and then randomly assign a label according to the node proportions, the probability of a correct label is

\[
\sum_k \hat p_k\hat p_k=\sum_k\hat p_k^2.
\]

Thus the probability of an incorrect label is

\[
1-\sum_k\hat p_k^2.
\]

A split divides \(S\) into \(S_L\) and \(S_R\). The weighted post-split impurity is

\[
G_{\text{split}}
=\frac{|S_L|}{|S|}G(S_L)+\frac{|S_R|}{|S|}G(S_R).
\]

The impurity reduction is

\[
\Delta G=G(S)-G_{\text{split}}.
\]

A tree chooses splits that increase class purity.

A random forest trains many trees on randomized subsets of samples and/or features. If tree \(t\) predicts class probabilities

\[
\hat p_t(z_i=k\mid x_i),
\]

then the forest probability is often the average:

\[
\hat p_{\text{RF}}(z_i=k\mid x_i)
=\frac{1}{T}\sum_{t=1}^T\hat p_t(z_i=k\mid x_i).
\]

If each tree votes for a class \(v_t\), then

\[
\hat p_{\text{RF}}(z_i=k\mid x_i)
=\frac{1}{T}\sum_{t=1}^T\mathbf 1\{v_t=k\}.
\]

These local probabilities become emission-like evidence in the RFMix sequence model.

## 2.4 From Random Forest Evidence to CRF Potentials

Let

\[
q_i(k)=\hat p_{\text{RF}}(z_i=k\mid x_i)
\]

be the random forest's local estimate. If we used only the forest, we would set

\[
\hat z_i=\arg\max_k q_i(k)
\]

independently for each \(i\). That ignores recombination. Instead define an observation potential

\[
\phi_i(k)=q_i(k).
\]

Because probabilities can be zero in finite forests, implementations may smooth:

\[
\phi_i(k)=\frac{v_i(k)+\epsilon}{T+K\epsilon},
\]

where \(v_i(k)\) is the number of tree votes for ancestry \(k\), \(T\) is the number of trees, and \(\epsilon>0\) prevents zero probabilities.

Now define a transition potential

\[
\tau_i(a,b)
\]

for moving from ancestry \(a\) at position \(i-1\) to ancestry \(b\) at position \(i\).

The RFMix-style sequence probability is then

\[
P(z\mid x)\propto
\prod_{i=1}^L \phi_i(z_i)
\prod_{i=2}^L \tau_i(z_{i-1},z_i).
\]

Normalize:

\[
P(z\mid x)=\frac{1}{Z(x)}
\prod_{i=1}^L \phi_i(z_i)
\prod_{i=2}^L \tau_i(z_{i-1},z_i).
\]

This is a linear-chain CRF with potentials shaped by random forest probabilities and recombination-aware transitions.

## 2.5 Deriving a Recombination Transition Model

Suppose positions \(i-1\) and \(i\) are separated by genetic distance \(d_i\) Morgans. One Morgan means an expected one recombination per meiosis over that interval. If recombination events follow a Poisson process with rate \(g d_i\) after \(g\) generations since admixture, then the number of recombinations \(R_i\) in that interval has distribution

\[
P(R_i=r)=\frac{(g d_i)^r e^{-g d_i}}{r!}.
\]

The probability of no recombination is

\[
P(R_i=0)=e^{-g d_i}.
\]

Therefore the probability of at least one recombination is

\[
P(R_i\ge 1)=1-P(R_i=0)=1-e^{-g d_i}.
\]

Let

\[
\rho_i=1-e^{-g d_i}.
\]

If no recombination occurs, ancestry remains the same. If recombination occurs, the new ancestry is drawn from genome-wide ancestry proportions

\[
\pi=(\pi_1,\ldots,\pi_K),\qquad \sum_k\pi_k=1.
\]

Then

\[
P(z_i=b\mid z_{i-1}=a)
=P(\text{no recomb})P(b\mid a,\text{no recomb})
+P(\text{recomb})P(b\mid \text{recomb}).
\]

If no recombination occurs,

\[
P(b\mid a,\text{no recomb})=\mathbf 1\{b=a\}.
\]

If recombination occurs,

\[
P(b\mid \text{recomb})=\pi_b.
\]

So

\[
P(z_i=b\mid z_{i-1}=a)
=(1-\rho_i)\mathbf 1\{b=a\}+\rho_i\pi_b.
\]

Since \(1-\rho_i=e^{-g d_i}\), this is

\[
P(z_i=b\mid z_{i-1}=a)
=e^{-g d_i}\mathbf 1\{b=a\}+(1-e^{-g d_i})\pi_b.
\]

This formula captures the essential intuition:

- if \(d_i\) is small, then \(e^{-g d_i}\) is near one and ancestry tends to persist;
- if \(d_i\) is large, a switch becomes more plausible;
- if \(g\) is large, many generations have allowed more recombination events, so ancestry tracts are shorter.

## 2.6 Full Sequence Probability

Use the local observation potentials \(\phi_i\) and transition probabilities \(T_i(a,b)\):

\[
T_i(a,b)=e^{-g d_i}\mathbf 1\{b=a\}+(1-e^{-g d_i})\pi_b.
\]

Then

\[
P(z\mid x)=\frac{1}{Z(x)}
\phi_1(z_1)\pi_{z_1}
\prod_{i=2}^L \phi_i(z_i)T_i(z_{i-1},z_i).
\]

The initial factor \(\pi_{z_1}\) says the starting ancestry is distributed according to genome-wide ancestry proportions. The partition function is

\[
Z(x)=\sum_z
\phi_1(z_1)\pi_{z_1}
\prod_{i=2}^L \phi_i(z_i)T_i(z_{i-1},z_i).
\]

Forward recursion:

\[
\alpha_1(k)=\pi_k\phi_1(k).
\]

For \(i\ge 2\),

\[
\alpha_i(b)=\phi_i(b)\sum_{a=1}^K \alpha_{i-1}(a)T_i(a,b).
\]

Finally,

\[
Z(x)=\sum_b\alpha_L(b).
\]

The posterior marginal is

\[
P(z_i=b\mid x)=\frac{\alpha_i(b)\beta_i(b)}{Z(x)}.
\]

The backward recursion is

\[
\beta_L(k)=1,
\]

and

\[
\beta_{i-1}(a)=\sum_{b=1}^K T_i(a,b)\phi_i(b)\beta_i(b).
\]

The maximum posterior sequence is found with Viterbi:

\[
\delta_1(k)=\log\pi_k+\log\phi_1(k),
\]

\[
\delta_i(b)=\log\phi_i(b)+\max_a[\delta_{i-1}(a)+\log T_i(a,b)].
\]

## 2.7 Diploid Local Ancestry

For a diploid individual, each locus has two ancestry labels:

\[
(z_i^{(1)},z_i^{(2)}).
\]

If haplotypes are phased and treated independently conditional on the observed data, one may run the model separately for each haplotype. If unphased genotype information is used, the hidden state can be the unordered ancestry pair:

\[
s_i=\{z_i^{(1)},z_i^{(2)}\}.
\]

There are

\[
\frac{K(K+1)}{2}
\]

unordered diploid states. For example, if \(K=3\), the states are

\[
\{1,1\},\{1,2\},\{1,3\},\{2,2\},\{2,3\},\{3,3\}.
\]

The same CRF/HMM-style recursions apply, but the state space is larger. If the two haplotypes transition independently, then

\[
P(s_i=(b_1,b_2)\mid s_{i-1}=(a_1,a_2))
=T_i(a_1,b_1)T_i(a_2,b_2)
\]

for ordered pairs. For unordered pairs, probabilities of equivalent orderings must be added.

## 2.8 Iterative Refinement

RFMix can use an expectation-maximization-like refinement idea. The initial reference panel trains the random forest. Then high-confidence inferred ancestry segments in admixed individuals can be added to the training information for later rounds.

Mathematically, let \(R^{(t)}\) be the reference-like labeled haplotypes at iteration \(t\). The random forest trained on \(R^{(t)}\) gives local probabilities

\[
q_i^{(t)}(k).
\]

The CRF gives posterior probabilities

\[
\gamma_i^{(t)}(k)=P^{(t)}(z_i=k\mid x).
\]

High-confidence calls satisfy

\[
\max_k\gamma_i^{(t)}(k)\ge c
\]

for some threshold \(c\). Those calls can augment the training data for iteration \(t+1\). The practical value is that admixed samples may contain long segments from ancestries not fully represented by small reference panels.

The danger is confirmation bias: wrong high-confidence calls can reinforce themselves. That is why thresholds, reference quality, and validation matter.

## 2.9 What RFMix Solves

RFMix tackles four major problems:

- It identifies ancestry changes along chromosomes, not only genome-wide admixture proportions.
- It uses haplotype context rather than single-marker evidence alone.
- It is computationally faster than many fully generative local ancestry methods.
- It combines flexible machine learning with recombination-aware smoothing.

Its limitations follow naturally from the derivation:

- If reference panels do not represent the true ancestral sources, local probabilities \(\phi_i(k)\) can be biased.
- If the generation parameter \(g\) is wrong, transition probabilities can oversmooth or oversegment.
- If populations are very closely related, local classifier evidence can be weak.
- If phasing is poor, haplotype-window features can degrade.

The core model remains elegant: local evidence from random forests, global coherence from a CRF.

# Chapter 3. String Kernels in Ancestry Analysis

## 3.1 Big Picture

A haplotype is a string. It may be a string over the alphabet \(\{0,1\}\), or over a larger alphabet if markers are multi-allelic. A DNA sequence is a string over \(\{A,C,G,T\}\). A sequence of local ancestry labels is a string over \(\{1,\ldots,K\}\).

String kernels provide a way to compare such objects without manually choosing a small set of summary statistics. Instead of saying "use allele \(i\), allele \(j\), and allele \(k\)," a string kernel can compare all substrings or subsequences of a certain type.

The central trick is:

\[
K(x,y)=\langle \phi(x),\phi(y)\rangle,
\]

where \(\phi(x)\) may be extremely high-dimensional, but \(K(x,y)\) can often be computed without explicitly storing all coordinates.

## 3.2 The Spectrum Kernel

Let \(\Sigma\) be an alphabet. For DNA,

\[
\Sigma=\{A,C,G,T\}.
\]

For biallelic haplotypes,

\[
\Sigma=\{0,1\}.
\]

Let \(\Sigma^k\) be the set of all strings of length \(k\). An element \(u\in\Sigma^k\) is called a \(k\)-mer.

For a string \(x\), define

\[
\phi_u(x)=\#\{\text{positions where }u\text{ occurs in }x\}.
\]

The feature map is

\[
\phi(x)=(\phi_u(x))_{u\in\Sigma^k}.
\]

The spectrum kernel is

\[
K_k(x,y)=\sum_{u\in\Sigma^k}\phi_u(x)\phi_u(y).
\]

This is the dot product of \(k\)-mer count vectors.

## 3.3 Positive Semidefinite Proof

We must prove this is a valid kernel. For any strings \(x_1,\ldots,x_n\) and real coefficients \(c_1,\ldots,c_n\),

\[
\sum_{i=1}^n\sum_{j=1}^n c_i c_jK_k(x_i,x_j)
=\sum_{i,j}c_ic_j\sum_{u}\phi_u(x_i)\phi_u(x_j).
\]

Swap the sums:

\[
=\sum_u\sum_{i,j}c_ic_j\phi_u(x_i)\phi_u(x_j).
\]

For fixed \(u\),

\[
\sum_{i,j}c_ic_j\phi_u(x_i)\phi_u(x_j)
=\left(\sum_i c_i\phi_u(x_i)\right)
\left(\sum_j c_j\phi_u(x_j)\right).
\]

The two parenthesized sums are the same scalar, so

\[
=\left(\sum_i c_i\phi_u(x_i)\right)^2.
\]

Therefore

\[
\sum_{i,j} c_i c_jK_k(x_i,x_j)
=\sum_u\left(\sum_i c_i\phi_u(x_i)\right)^2\ge 0.
\]

Each term is a square, so the sum is nonnegative. Thus the spectrum kernel is positive semidefinite.

## 3.4 A Haplotype Example

Let

\[
x=00101,\qquad y=10101.
\]

Use \(k=2\). The possible 2-mers are

\[
00,01,10,11.
\]

For \(x=00101\), the length-2 windows are

\[
00,\;01,\;10,\;01.
\]

So

\[
\phi(x)=(1,2,1,0)
\]

in the order \((00,01,10,11)\).

For \(y=10101\), the windows are

\[
10,\;01,\;10,\;01.
\]

So

\[
\phi(y)=(0,2,2,0).
\]

The kernel is

\[
K_2(x,y)=1\cdot0+2\cdot2+1\cdot2+0\cdot0=6.
\]

This number is large when the two haplotypes share many local patterns.

## 3.5 Normalization

Longer strings tend to have larger \(k\)-mer counts. To compare strings of different length or different missingness, normalize:

\[
\tilde K(x,y)=\frac{K(x,y)}{\sqrt{K(x,x)K(y,y)}}.
\]

Why this formula? Since

\[
K(x,y)=\langle \phi(x),\phi(y)\rangle,
\]

and

\[
K(x,x)=\langle \phi(x),\phi(x)\rangle=\|\phi(x)\|^2,
\]

we have

\[
\tilde K(x,y)=
\frac{\langle \phi(x),\phi(y)\rangle}
{\|\phi(x)\|\|\phi(y)\|}.
\]

This is the cosine of the angle between feature vectors. It lies between \(-1\) and \(1\), and for nonnegative count vectors it lies between \(0\) and \(1\).

## 3.6 The Mismatch Kernel

Exact \(k\)-mer matching can be too strict. In genetic data, mutation, genotyping error, or recombination can make closely related haplotypes differ at a few sites.

For two \(k\)-mers \(u\) and \(v\), define Hamming distance:

\[
d_H(u,v)=\#\{r:u_r\ne v_r\}.
\]

The \((k,m)\)-mismatch feature for \(u\) counts all observed \(k\)-mers within \(m\) mismatches of \(u\):

\[
\phi_u^{(m)}(x)=\sum_{\text{k-mer }v\text{ in }x}\mathbf 1\{d_H(u,v)\le m\}.
\]

The mismatch kernel is

\[
K_{k,m}(x,y)=\sum_{u\in\Sigma^k}\phi_u^{(m)}(x)\phi_u^{(m)}(y).
\]

The positive semidefinite proof is identical to the spectrum-kernel proof, because this is again an inner product of feature vectors.

## 3.7 Weighted Degree Kernel

Genetic markers are ordered. A \(k\)-mer at one genomic location is not equivalent to the same \(k\)-mer at a distant location if markers are aligned by position. A weighted degree kernel preserves position:

\[
K(x,y)=\sum_{\ell=1}^d \beta_\ell\sum_{i=1}^{L-\ell+1}
\mathbf 1\{x_{i:i+\ell-1}=y_{i:i+\ell-1}\}.
\]

Here:

- \(\ell\) is substring length;
- \(\beta_\ell\ge 0\) is a weight;
- \(x_{i:i+\ell-1}\) is the substring of \(x\) beginning at \(i\).

This kernel gives credit for matching substrings of different lengths at the same position. Longer matches can be weighted more heavily if they are more ancestry-informative.

To prove positive semidefiniteness, define a feature coordinate for each pair \((i,u,\ell)\):

\[
\phi_{i,u,\ell}(x)=\sqrt{\beta_\ell}\mathbf 1\{x_{i:i+\ell-1}=u\}.
\]

Then

\[
\langle\phi(x),\phi(y)\rangle
=\sum_{\ell,i,u}\beta_\ell
\mathbf 1\{x_{i:i+\ell-1}=u\}
\mathbf 1\{y_{i:i+\ell-1}=u\}.
\]

The product of indicators is one exactly when both substrings equal the same \(u\), which is exactly when they equal each other. Therefore

\[
\langle\phi(x),\phi(y)\rangle=K(x,y).
\]

Since it is an inner product, it is a valid kernel.

## 3.8 Subsequence Kernels

The spectrum kernel uses contiguous substrings. A subsequence kernel allows gaps. Let \(u=(u_1,\ldots,u_k)\) be a length-\(k\) string. It occurs as a subsequence in \(x\) if there are indices

\[
1\le i_1<i_2<\cdots<i_k\le |x|
\]

such that

\[
x_{i_r}=u_r
\]

for all \(r\). Gaps are penalized by a decay parameter \(0<\lambda\le 1\).

For one occurrence \(I=(i_1,\ldots,i_k)\), define its span:

\[
\ell(I)=i_k-i_1+1.
\]

The feature is

\[
\phi_u(x)=\sum_{I:u=x_I}\lambda^{\ell(I)}.
\]

The subsequence kernel is

\[
K(x,y)=\sum_{u\in\Sigma^k}\phi_u(x)\phi_u(y).
\]

Again, this is an inner product. The challenge is computation: there are many subsequences. Dynamic programming can compute the kernel without enumerating all of them.

## 3.9 Kernel Machines for Ancestry Classification

Suppose each individual or haplotype string \(x_i\) has a population label

\[
y_i\in\{-1,+1\}.
\]

A linear classifier in feature space uses

\[
f(x)=w^T\phi(x)+b.
\]

The predicted label is

\[
\hat y=\operatorname{sign}(f(x)).
\]

Support vector machines choose a separating hyperplane with large margin. The primal soft-margin problem is

\[
\min_{w,b,\xi}
\frac{1}{2}\|w\|^2+C\sum_{i=1}^n\xi_i
\]

subject to

\[
y_i(w^T\phi(x_i)+b)\ge 1-\xi_i,\qquad \xi_i\ge 0.
\]

The slack variable \(\xi_i\) allows misclassification or small margins. The parameter \(C\) controls the cost of violations.

Introduce Lagrange multipliers \(\alpha_i\ge 0\) for the margin constraints and \(\mu_i\ge 0\) for \(\xi_i\ge 0\). The Lagrangian is

\[
\mathcal L=
\frac{1}{2}\|w\|^2+C\sum_i\xi_i
-\sum_i\alpha_i[y_i(w^T\phi(x_i)+b)-1+\xi_i]
-\sum_i\mu_i\xi_i.
\]

Differentiate with respect to \(w\):

\[
\frac{\partial\mathcal L}{\partial w}
=w-\sum_i\alpha_i y_i\phi(x_i).
\]

Set to zero:

\[
w=\sum_i\alpha_i y_i\phi(x_i).
\]

Differentiate with respect to \(b\):

\[
\frac{\partial\mathcal L}{\partial b}
=-\sum_i\alpha_i y_i.
\]

Set to zero:

\[
\sum_i\alpha_i y_i=0.
\]

Differentiate with respect to \(\xi_i\):

\[
\frac{\partial\mathcal L}{\partial \xi_i}
=C-\alpha_i-\mu_i.
\]

Since \(\mu_i\ge0\), this gives

\[
0\le\alpha_i\le C.
\]

Substitute \(w=\sum_i\alpha_i y_i\phi(x_i)\) into the Lagrangian. The dual objective becomes

\[
\max_\alpha
\sum_i\alpha_i-\frac{1}{2}\sum_i\sum_j
\alpha_i\alpha_j y_i y_j
\langle\phi(x_i),\phi(x_j)\rangle
\]

subject to

\[
0\le\alpha_i\le C,\qquad \sum_i\alpha_i y_i=0.
\]

Replace the inner product with the kernel:

\[
\max_\alpha
\sum_i\alpha_i-\frac{1}{2}\sum_i\sum_j
\alpha_i\alpha_j y_i y_jK(x_i,x_j).
\]

The classifier is

\[
f(x)=\sum_i\alpha_i y_iK(x_i,x)+b.
\]

This is the kernel trick: the algorithm needs only pairwise string similarities.

## 3.10 Uses in Ancestry Analysis

String kernels can support ancestry analysis in several ways:

- population assignment from haplotype strings;
- nearest-neighbor ancestry matching using kernel similarity;
- clustering or visualization with kernel PCA;
- comparing distributions of haplotypes across populations;
- constructing features for supervised local ancestry models.

They are especially useful when ancestry information is encoded in patterns across markers rather than isolated allele frequencies.

## 3.11 Challenges and Caveats

String kernels also have limitations:

- Haplotype strings must usually be aligned and quality controlled.
- Missing data require careful handling.
- Kernel choice strongly affects what similarity means.
- A kernel can measure similarity without explaining demographic history.
- Relatedness, linkage disequilibrium, and ascertainment bias can dominate naive similarity measures.

The big picture is that string kernels give a flexible representation layer. They do not replace demographic modeling, but they can make sequence-like ancestry information available to kernel methods.

# Chapter 4. qpGraph

## 4.1 Big Picture

qpGraph fits admixture graphs to allele-frequency data. The graph contains population splits, genetic drift along edges, and admixture events. The data are summarized by f-statistics, especially \(f_2\), \(f_3\), and \(f_4\).

The goal is not to reconstruct every individual genealogy. Instead, qpGraph asks:

\[
\text{Can this proposed population graph explain the observed allele-frequency correlations?}
\]

The graph is a hypothesis. The f-statistics are moment summaries. qpGraph fits drift lengths and admixture proportions so the predicted moments match observed moments.

## 4.2 Allele Frequencies as Random Variables

At SNP \(\ell\), let \(p_A(\ell)\) be the allele frequency in population \(A\). Across SNPs, allele frequencies vary. f-statistics average functions of these frequencies over many SNPs.

For two populations \(A\) and \(B\), define

\[
f_2(A,B)=\mathbb E_\ell[(p_A(\ell)-p_B(\ell))^2].
\]

In practice, the expectation is estimated by an average over SNPs:

\[
\hat f_2(A,B)=\frac{1}{M}\sum_{\ell=1}^M
(\hat p_A(\ell)-\hat p_B(\ell))^2
\]

with corrections for finite sample size in real implementations.

The statistic \(f_2\) is a squared distance between allele frequencies.

## 4.3 Drift Model on a Tree

Imagine an ancestral population with allele frequency \(p_0\). Along an edge \(e\), allele frequency changes by a random drift increment \(\Delta_e\). If population \(A\) is reached by following a path from the root, then

\[
p_A=p_0+\sum_{e\in \operatorname{path}(A)}\Delta_e.
\]

Assume:

1. \(\mathbb E[\Delta_e]=0\);
2. \(\Delta_e\) and \(\Delta_{e'}\) are uncorrelated for distinct edges;
3. \(\mathbb E[\Delta_e^2]=d_e\), the drift length of edge \(e\).

For populations \(A\) and \(B\),

\[
p_A-p_B=
\sum_{e\in \operatorname{path}(A)}\Delta_e
-\sum_{e\in \operatorname{path}(B)}\Delta_e.
\]

Edges shared by both paths cancel. Only edges on the path between \(A\) and \(B\) remain. Therefore

\[
p_A-p_B=\sum_{e\in A\leftrightarrow B} s_e\Delta_e,
\]

where \(s_e\in\{-1,+1\}\) indicates orientation.

Now

\[
f_2(A,B)=\mathbb E[(p_A-p_B)^2].
\]

Substitute:

\[
f_2(A,B)=
\mathbb E\left[
\left(\sum_{e\in A\leftrightarrow B}s_e\Delta_e\right)^2
\right].
\]

Expand the square:

\[
=\mathbb E\left[
\sum_e\sum_{e'}s_es_{e'}\Delta_e\Delta_{e'}
\right].
\]

Move expectation inside:

\[
=\sum_e\sum_{e'}s_es_{e'}\mathbb E[\Delta_e\Delta_{e'}].
\]

For \(e\ne e'\), the increments are uncorrelated, so

\[
\mathbb E[\Delta_e\Delta_{e'}]=0.
\]

For \(e=e'\),

\[
\mathbb E[\Delta_e^2]=d_e.
\]

Thus

\[
f_2(A,B)=\sum_{e\in A\leftrightarrow B}d_e.
\]

This is the additivity of drift distance on a tree.

## 4.4 The f3 Statistic

The \(f_3\) statistic is

\[
f_3(C;A,B)=\mathbb E[(p_C-p_A)(p_C-p_B)].
\]

If \(C\) is admixed between sources related to \(A\) and \(B\), \(f_3(C;A,B)\) can be negative. That is why \(f_3\) is used as an admixture test.

To see the algebra, suppose

\[
p_C=\alpha p_A+(1-\alpha)p_B+\epsilon,
\]

where \(\epsilon\) is drift after admixture and is independent of source differences. Then

\[
p_C-p_A=(1-\alpha)(p_B-p_A)+\epsilon.
\]

Also

\[
p_C-p_B=\alpha(p_A-p_B)+\epsilon.
\]

Let

\[
D=p_A-p_B.
\]

Then \(p_B-p_A=-D\). So

\[
p_C-p_A=-(1-\alpha)D+\epsilon,
\]

and

\[
p_C-p_B=\alpha D+\epsilon.
\]

Multiply:

\[
(p_C-p_A)(p_C-p_B)
=[-(1-\alpha)D+\epsilon][\alpha D+\epsilon].
\]

Expand:

\[
=-\alpha(1-\alpha)D^2-(1-\alpha)D\epsilon+\alpha D\epsilon+\epsilon^2.
\]

Take expectation:

\[
f_3(C;A,B)
=-\alpha(1-\alpha)\mathbb E[D^2]
 +(-1+\alpha+\alpha)\mathbb E[D\epsilon]
 +\mathbb E[\epsilon^2].
\]

If \(D\) and \(\epsilon\) are uncorrelated,

\[
\mathbb E[D\epsilon]=0.
\]

Therefore

\[
f_3(C;A,B)
=-\alpha(1-\alpha)f_2(A,B)+\mathbb E[\epsilon^2].
\]

The first term is negative. If post-admixture drift is not too large, the statistic becomes negative, giving evidence of admixture.

## 4.5 The f4 Statistic

The \(f_4\) statistic is

\[
f_4(A,B;C,D)=\mathbb E[(p_A-p_B)(p_C-p_D)].
\]

It measures whether the allele-frequency difference between \(A\) and \(B\) is correlated with the difference between \(C\) and \(D\).

If the tree topology is \(((A,B),(C,D))\) with no admixture, then the drift separating \(A\) from \(B\) is independent of the drift separating \(C\) from \(D\), so

\[
f_4(A,B;C,D)=0.
\]

If \(A\) and \(C\) share extra ancestry not shared with \(B\) and \(D\), the statistic becomes nonzero.

## 4.6 f4 as Shared Drift

Using the drift model, write each population as

\[
p_X=p_0+\sum_e c_{X,e}\Delta_e,
\]

where \(c_{X,e}\) is the contribution of edge \(e\) to population \(X\). On a tree, \(c_{X,e}=1\) if \(e\) lies on the path from root to \(X\), otherwise \(0\). With admixture, \(c_{X,e}\) can be a mixture coefficient.

Then

\[
p_A-p_B=\sum_e(c_{A,e}-c_{B,e})\Delta_e,
\]

and

\[
p_C-p_D=\sum_e(c_{C,e}-c_{D,e})\Delta_e.
\]

Multiply:

\[
(p_A-p_B)(p_C-p_D)
=\sum_e\sum_{e'}
(c_{A,e}-c_{B,e})(c_{C,e'}-c_{D,e'})
\Delta_e\Delta_{e'}.
\]

Take expectation:

\[
f_4(A,B;C,D)
=\sum_e\sum_{e'}
(c_{A,e}-c_{B,e})(c_{C,e'}-c_{D,e'})
\mathbb E[\Delta_e\Delta_{e'}].
\]

Only \(e=e'\) terms remain:

\[
f_4(A,B;C,D)
=\sum_e
(c_{A,e}-c_{B,e})(c_{C,e}-c_{D,e})d_e.
\]

This formula is the heart of qpGraph. Given a graph, every population has coefficients \(c_{X,e}\) for every drift edge. The graph predicts f-statistics by summing drift lengths times products of coefficients.

## 4.7 Modeling Admixture Coefficients

Suppose population \(C\) is an admixture of two parental lineages \(A\) and \(B\):

\[
p_C=\alpha p_A+(1-\alpha)p_B+\epsilon_C.
\]

For any earlier edge \(e\), if the coefficient in \(A\) is \(c_{A,e}\) and in \(B\) is \(c_{B,e}\), then the coefficient in \(C\) is

\[
c_{C,e}=\alpha c_{A,e}+(1-\alpha)c_{B,e}.
\]

For the post-admixture drift edge unique to \(C\), \(c_{C,e}=1\) and other populations have coefficient \(0\), unless they descend from \(C\).

Thus admixture makes graph coefficients linear combinations. f-statistics are nonlinear in admixture proportions because products such as

\[
(c_{A,e}-c_{B,e})(c_{C,e}-c_{D,e})
\]

contain the coefficients.

## 4.8 qpGraph Objective Function

Let \(s\) be the vector of observed f-statistics, and let

\[
\mu(\theta)
\]

be the vector predicted by a graph with parameters \(\theta\), including drift lengths and admixture proportions.

The residual is

\[
r(\theta)=s-\mu(\theta).
\]

If \(\Sigma\) is the covariance matrix of the estimated statistics, qpGraph uses a weighted fit:

\[
Q(\theta)=r(\theta)^T\Sigma^{-1}r(\theta).
\]

Why this form? If

\[
s\sim N(\mu(\theta),\Sigma),
\]

then the multivariate normal density is

\[
p(s\mid\theta)=
\frac{1}{(2\pi)^{m/2}|\Sigma|^{1/2}}
\exp\left[-\frac{1}{2}(s-\mu(\theta))^T\Sigma^{-1}(s-\mu(\theta))\right].
\]

Taking logs:

\[
\log p(s\mid\theta)
=-\frac{m}{2}\log(2\pi)-\frac{1}{2}\log|\Sigma|
-\frac{1}{2}r(\theta)^T\Sigma^{-1}r(\theta).
\]

The first two terms do not depend on \(\theta\), so maximizing the log-likelihood is equivalent to minimizing

\[
r(\theta)^T\Sigma^{-1}r(\theta).
\]

## 4.9 Block Jackknife

Allele-frequency statistics are correlated across nearby SNPs because of linkage disequilibrium. A common uncertainty method is the block jackknife.

Divide the genome into \(B\) blocks. Let \(\hat s\) be the estimate using all blocks. Let \(\hat s_{(-b)}\) be the estimate leaving out block \(b\).

The jackknife mean is

\[
\bar s_{(-\cdot)}=\frac{1}{B}\sum_{b=1}^B\hat s_{(-b)}.
\]

The jackknife covariance estimate is

\[
\hat\Sigma=
\frac{B-1}{B}
\sum_{b=1}^B
(\hat s_{(-b)}-\bar s_{(-\cdot)})
(\hat s_{(-b)}-\bar s_{(-\cdot)})^T.
\]

The factor \((B-1)/B\) appears because leave-one-block estimates are highly overlapping; the jackknife rescales their variability to estimate the variability of the full-sample statistic.

## 4.10 What qpGraph Solves

qpGraph addresses the problem of historical model fitting:

- Did a proposed set of splits and admixture events plausibly generate the observed allele-frequency correlations?
- What drift lengths are implied?
- What admixture proportions are implied?
- Which residuals reveal graph misspecification?

It is powerful because f-statistics compress genome-wide data into interpretable moments. It is dangerous when overinterpreted: many graphs can fit the same statistics, and a fitted graph is not a unique true history.

## 4.11 Identifiability and Model Risk

An admixture graph can fail for several reasons:

- The true sources are unsampled.
- The graph topology is wrong.
- Different histories produce similar f-statistics.
- Drift lengths or admixture proportions lie near boundaries.
- SNP ascertainment affects allele-frequency moments.

Mathematically, non-identifiability means there may exist distinct parameter values \(\theta_1\ne\theta_2\) such that

\[
\mu(\theta_1)=\mu(\theta_2).
\]

If the predicted statistics are identical, the data summarized by those statistics cannot distinguish the models.

The correct interpretation of qpGraph is therefore comparative and diagnostic. It tests whether a proposed graph is consistent with a set of moment constraints; it does not prove that the graph is the only possible history.

# Chapter 5. qpAdm

## 5.1 Big Picture

qpAdm tests whether a target population can be modeled as a mixture of specified source populations, using a set of outgroup or reference populations. It is closely related to qpWave.

The input is divided into:

- left populations: target plus proposed sources;
- right populations: outgroups used to detect ancestry differences.

The main question is:

\[
\text{Can the target be represented as a mixture of the proposed sources with respect to the right populations?}
\]

If yes, qpAdm estimates mixture weights. If no, it rejects the model.

## 5.2 The f4 Matrix

Let the left populations be

\[
L_0,L_1,\ldots,L_m,
\]

where \(L_0\) is the target and \(L_1,\ldots,L_m\) are candidate sources.

Let the right populations be

\[
R_0,R_1,\ldots,R_n.
\]

Choose baseline populations \(L_0\) and \(R_0\). Construct a matrix \(F\) with entries

\[
F_{ij}=f_4(L_i,L_0;R_j,R_0)
\]

for

\[
i=1,\ldots,m,\qquad j=1,\ldots,n.
\]

This matrix summarizes how left-population differences relate to right-population differences.

## 5.3 qpWave Rank Idea

qpWave asks how many ancestry streams connect the left set to the right set. If the rank of the f4 matrix is \(r\), then roughly \(r\) independent dimensions of ancestry differentiation are needed.

The mathematical statement is:

\[
\operatorname{rank}(F)\le r.
\]

If a matrix has rank \(r\), all its columns lie in an \(r\)-dimensional subspace. Equivalently, all \((r+1)\times(r+1)\) determinants vanish.

Why does low rank correspond to few ancestry streams? Suppose each left population can be represented by coefficients over \(q\) ancestry streams, and each right contrast measures those streams. Then

\[
F=A B^T,
\]

where \(A\) is an \(m\times q\) matrix of left coefficients and \(B\) is an \(n\times q\) matrix of right sensitivities. A product \(AB^T\) has rank at most \(q\), because its columns lie in the column space of \(A\). Therefore

\[
\operatorname{rank}(F)\le q.
\]

This is the algebraic bridge between f4 matrices and ancestry-stream counts.

## 5.4 qpAdm Mixture Model

Suppose the target \(T\) is a mixture of \(m\) sources \(S_1,\ldots,S_m\):

\[
p_T=\sum_{a=1}^m w_a p_{S_a}+\epsilon,
\]

where

\[
\sum_{a=1}^m w_a=1.
\]

The vector \(\epsilon\) represents drift after admixture that is not shared with the right populations. For a right-population contrast \((R_j,R_0)\), consider

\[
f_4(T,S_m;R_j,R_0).
\]

Using linearity of expectation, allele-frequency differences involving \(T\) can be expressed in terms of source differences.

Start with

\[
p_T-p_{S_m}=\sum_{a=1}^m w_a p_{S_a}-p_{S_m}+\epsilon.
\]

Since

\[
\sum_{a=1}^m w_a=1,
\]

we can write

\[
p_{S_m}=\sum_{a=1}^m w_a p_{S_m}.
\]

Therefore

\[
p_T-p_{S_m}
=\sum_{a=1}^m w_a(p_{S_a}-p_{S_m})+\epsilon.
\]

The term for \(a=m\) is

\[
w_m(p_{S_m}-p_{S_m})=0.
\]

So

\[
p_T-p_{S_m}
=\sum_{a=1}^{m-1} w_a(p_{S_a}-p_{S_m})+\epsilon.
\]

Now multiply by the right contrast:

\[
(p_T-p_{S_m})(p_{R_j}-p_{R_0})
=
\left[
\sum_{a=1}^{m-1} w_a(p_{S_a}-p_{S_m})+\epsilon
\right]
(p_{R_j}-p_{R_0}).
\]

Take expectation:

\[
f_4(T,S_m;R_j,R_0)
=
\sum_{a=1}^{m-1}w_a f_4(S_a,S_m;R_j,R_0)
+\mathbb E[\epsilon(p_{R_j}-p_{R_0})].
\]

If post-admixture drift \(\epsilon\) is not shared with the right populations, then

\[
\mathbb E[\epsilon(p_{R_j}-p_{R_0})]=0.
\]

Thus

\[
f_4(T,S_m;R_j,R_0)
=
\sum_{a=1}^{m-1}w_a f_4(S_a,S_m;R_j,R_0).
\]

This is the core qpAdm linear model.

## 5.5 Solving for Weights

Let \(b\in\mathbb R^n\) be the vector

\[
b_j=f_4(T,S_m;R_j,R_0).
\]

Let \(A\in\mathbb R^{n\times(m-1)}\) have entries

\[
A_{j,a}=f_4(S_a,S_m;R_j,R_0).
\]

Let

\[
w'=(w_1,\ldots,w_{m-1})^T.
\]

The model is

\[
b=Aw'.
\]

If \(n=m-1\) and \(A\) is invertible,

\[
w'=A^{-1}b.
\]

Usually \(n>m-1\), so the system is overdetermined. Use weighted least squares:

\[
\hat w'=\arg\min_{w'}(b-Aw')^T\Sigma^{-1}(b-Aw').
\]

Differentiate. Let

\[
Q(w')=(b-Aw')^T\Sigma^{-1}(b-Aw').
\]

Expand:

\[
Q=b^T\Sigma^{-1}b
-b^T\Sigma^{-1}Aw'
-(w')^TA^T\Sigma^{-1}b
+(w')^TA^T\Sigma^{-1}Aw'.
\]

Since \(Q\) is scalar,

\[
b^T\Sigma^{-1}Aw'=(w')^TA^T\Sigma^{-1}b.
\]

So

\[
Q=b^T\Sigma^{-1}b
-2(w')^TA^T\Sigma^{-1}b
+(w')^TA^T\Sigma^{-1}Aw'.
\]

Differentiate:

\[
\frac{\partial Q}{\partial w'}
=-2A^T\Sigma^{-1}b+2A^T\Sigma^{-1}Aw'.
\]

Set to zero:

\[
A^T\Sigma^{-1}Aw'=A^T\Sigma^{-1}b.
\]

If \(A^T\Sigma^{-1}A\) is invertible,

\[
\hat w'=(A^T\Sigma^{-1}A)^{-1}A^T\Sigma^{-1}b.
\]

The final weight is

\[
\hat w_m=1-\sum_{a=1}^{m-1}\hat w_a.
\]

## 5.6 Standard Errors

Under the linear model

\[
b=Aw'+\eta,\qquad \eta\sim N(0,\Sigma),
\]

the weighted least-squares estimator is

\[
\hat w'=(A^T\Sigma^{-1}A)^{-1}A^T\Sigma^{-1}b.
\]

For compactness, define

\[
M=(A^T\Sigma^{-1}A)^{-1}A^T\Sigma^{-1}.
\]

Substitute \(b=Aw'+\eta\):

\[
\hat w'
=(A^T\Sigma^{-1}A)^{-1}A^T\Sigma^{-1}(Aw'+\eta).
\]

Distribute:

\[
\hat w'
=(A^T\Sigma^{-1}A)^{-1}A^T\Sigma^{-1}Aw'
+(A^T\Sigma^{-1}A)^{-1}A^T\Sigma^{-1}\eta.
\]

The first term simplifies:

\[
(A^T\Sigma^{-1}A)^{-1}(A^T\Sigma^{-1}A)w'=w'.
\]

Thus

\[
\hat w'-w'=(A^T\Sigma^{-1}A)^{-1}A^T\Sigma^{-1}\eta.
\]

The covariance is

\[
\operatorname{Cov}(\hat w')
=(A^T\Sigma^{-1}A)^{-1}A^T\Sigma^{-1}
\operatorname{Cov}(\eta)
\Sigma^{-1}A(A^T\Sigma^{-1}A)^{-1}.
\]

Since \(\operatorname{Cov}(\eta)=\Sigma\),

\[
\operatorname{Cov}(\hat w')
=(A^T\Sigma^{-1}A)^{-1}A^T\Sigma^{-1}
\Sigma
\Sigma^{-1}A(A^T\Sigma^{-1}A)^{-1}.
\]

The middle terms simplify:

\[
\Sigma^{-1}\Sigma\Sigma^{-1}=\Sigma^{-1}.
\]

Therefore

\[
\operatorname{Cov}(\hat w')
=(A^T\Sigma^{-1}A)^{-1}A^T\Sigma^{-1}A(A^T\Sigma^{-1}A)^{-1}.
\]

Finally,

\[
\operatorname{Cov}(\hat w')
=(A^T\Sigma^{-1}A)^{-1}.
\]

In practice, qpAdm uses block-jackknife machinery because \(A\), \(b\), and \(\Sigma\) are estimated from genetic data rather than known exactly.

## 5.7 Model Fit Test

The residual is

\[
\hat r=b-A\hat w'.
\]

The weighted residual sum is

\[
Q=\hat r^T\Sigma^{-1}\hat r.
\]

If the model is correct and regularity assumptions hold, \(Q\) is approximately chi-square distributed with degrees of freedom

\[
\nu=n-(m-1),
\]

because \(n\) right-population contrasts are fitted using \(m-1\) free weights. The p-value is

\[
p=P(\chi^2_\nu\ge Q).
\]

A small p-value indicates that the proposed sources cannot explain the target's relationship to the right populations under the model assumptions.

## 5.8 Why Outgroups Matter

The right populations define the axes along which the model is tested. If the right set is weak, a bad model can pass. If the right set includes populations that detect ancestry differences missing from the sources, the model is more likely to fail appropriately.

Mathematically, if the residual vector lies in directions not measured by the right populations, then

\[
\hat r\approx 0
\]

even if the historical interpretation is wrong. Adding informative right populations expands the contrast space.

## 5.9 Feasible but Invalid Weights

qpAdm may return weights outside \([0,1]\). A two-source model might estimate

\[
\hat w_1=1.15,\qquad \hat w_2=-0.15.
\]

The algebraic model can still fit f4 statistics, but negative ancestry proportions are not biologically meaningful in a simple mixture interpretation. Such a result usually means:

- the proposed sources are proxies rather than true sources;
- source order or right-population choice creates extrapolation;
- the target is not actually modeled by those sources;
- sampling noise is large.

One can impose constraints, but constrained optimization changes the null distribution of test statistics. Interpretation must be careful.

## 5.10 What qpAdm Solves

qpAdm solves a narrower but very useful problem than qpGraph:

- It does not require specifying a full admixture graph.
- It tests a target-source model using outgroup contrasts.
- It estimates mixture weights.
- It separates source candidates from right-population references.

Its practical strength is that it allows many targeted hypotheses to be tested without fitting a full graph each time.

## 5.11 Main Assumptions and Risks

The qpAdm derivation depends on assumptions:

- the target is a mixture of the proposed sources or close proxies;
- post-admixture drift in the target is not correlated with right-population contrasts;
- right populations are appropriately chosen;
- SNP ascertainment and missing data do not distort f-statistics beyond correction;
- block jackknife uncertainty is adequate;
- sources are not so collinear that weights become unstable.

Collinearity can be expressed algebraically. If columns of \(A\) are nearly linearly dependent, then \(A^T\Sigma^{-1}A\) is nearly singular. Its inverse has large entries, making

\[
\operatorname{Cov}(\hat w')=(A^T\Sigma^{-1}A)^{-1}
\]

large. This produces unstable weights and wide standard errors.

# Comparative Summary

The five models live at different levels:

| Method | Main object | Main mathematical form | Main goal |
|---|---|---|---|
| CRF | label sequence | \(P(y\mid x)\propto\prod_i\psi_i(y_{i-1},y_i,x)\) | structured prediction |
| RFMix | local ancestry sequence | random forest evidence plus CRF transitions | infer ancestry tracts |
| String kernels | strings/haplotypes | \(K(x,y)=\langle\phi(x),\phi(y)\rangle\) | compare sequence-like genetic objects |
| qpGraph | population graph | predicted f-statistics from drift/admixture graph | fit historical graph |
| qpAdm | target-source model | linear f4 constraints and rank tests | test admixture model and estimate weights |

They answer different questions:

- CRF: how do we label a structured sequence?
- RFMix: where along the genome did ancestry come from?
- String kernels: how similar are haplotypes or sequences under a chosen feature representation?
- qpGraph: is a proposed population history graph consistent with allele-frequency moments?
- qpAdm: can a target be modeled as a mixture of specified sources relative to outgroups?

# Practical Research Notes

1. CRFs and RFMix are individual- or haplotype-level sequence models. They operate along chromosomes.
2. qpGraph and qpAdm are population-level moment models. They operate on allele-frequency summaries across populations.
3. String kernels can operate at either level, depending on whether strings represent individuals, haplotypes, windows, or populations.
4. A local ancestry call from RFMix can later be summarized into ancestry tracts and proportions, but it is not the same kind of evidence as qpAdm f4 constraints.
5. qpAdm and qpGraph can test population-level histories, but they do not label ancestry at each locus.

# Glossary

- Admixture: formation of a population from multiple ancestral sources.
- Allele frequency: frequency of an allele in a population.
- CRF: conditional random field, a conditional model for structured labels.
- Drift: random allele-frequency change over generations.
- f-statistics: allele-frequency moment statistics used to study population relationships.
- Haplotype: sequence of alleles inherited together on one chromosome.
- Kernel: similarity function corresponding to an inner product in feature space.
- Local ancestry: ancestry label at a specific genomic region.
- Outgroup: reference population used to orient or test ancestry relationships.
- Partition function: normalizing sum that turns unnormalized scores into probabilities.
- Positive semidefinite: property ensuring a kernel is a valid inner product kernel.
- qpAdm: ADMIXTOOLS method for admixture-source testing and weight estimation.
- qpGraph: ADMIXTOOLS method for fitting admixture graphs to f-statistics.
- Random forest: ensemble of randomized decision trees.

# Bibliography

Lafferty, J., McCallum, A., and Pereira, F. 2001. Conditional Random Fields: Probabilistic Models for Segmenting and Labeling Sequence Data. https://repository.upenn.edu/entities/publication/c8b4b2a3-cc00-4e08-851f-0caa55b8fefe

Sutton, C., and McCallum, A. 2010. An Introduction to Conditional Random Fields. https://arxiv.org/abs/1011.4088

Maples, B. K., Gravel, S., Kenny, E. E., and Bustamante, C. D. 2013. RFMix: A Discriminative Modeling Approach for Rapid and Robust Local-Ancestry Inference. American Journal of Human Genetics. https://www.cell.com/ajhg/fulltext/S0002-9297(13)00289-9

RFMix repository. https://github.com/slowkoni/rfmix

Lodhi, H., Saunders, C., Shawe-Taylor, J., Cristianini, N., and Watkins, C. 2002. Text Classification using String Kernels. Journal of Machine Learning Research. https://www.jmlr.org/papers/v2/lodhi02a.html

Leslie, C., Eskin, E., and Noble, W. S. 2002. The spectrum kernel: a string kernel for SVM protein classification. https://psb.stanford.edu/psb-online/proceedings/psb02/leslie.pdf

Patterson, N. et al. 2012. Ancient Admixture in Human History. Genetics. https://pmc.ncbi.nlm.nih.gov/articles/PMC3522152/

Maier, R. et al. ADMIXTOOLS 2 documentation: qpGraph. https://uqrmaie1.github.io/admixtools/articles/qpgraph.html

Maier, R. et al. ADMIXTOOLS 2 documentation: qpAdm. https://uqrmaie1.github.io/admixtools/articles/qpadm.html

Maier, R. et al. 2023. ADMIXTOOLS 2: fast and accurate population history inference. Genetics. https://academic.oup.com/genetics/article/216/4/913/6065872

Harney, E. et al. 2021. Assessing the performance of qpAdm. https://pmc.ncbi.nlm.nih.gov/articles/PMC8248411/
