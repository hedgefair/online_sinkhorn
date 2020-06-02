import numpy as np

from onlikhorn.dataset import get_dragon, create_sphere


class Subsampler:
    def __init__(self, x=None, size=None, cycle=True, small_last=False, return_idx=False):
        if return_idx:
            self.x = np.arange(size, dtype=np.long)
        else:
            self.x = np.array(x, copy=True)
        np.random.shuffle(self.x)
        self.cursor = 0
        self.cycle = cycle
        self.small_last = small_last
        self.return_idx = False

    def __call__(self, n):
        if not self.cycle:
            x = self.x[np.random.permutation(len(self.x))[:n]]
        else:
            new_cursor = min(len(self.x), self.cursor + n)
            x = np.array(self.x[self.cursor:new_cursor], copy=True)
            if new_cursor == len(self.x):
                np.random.shuffle(self.x)
                if self.small_last:
                    self.cursor = 0
                else:
                    self.cursor = (self.cursor + n) % len(self.x)
                    x = np.concatenate([x, self.x[:self.cursor]], axis=0)
            else:
                self.cursor = new_cursor
        n = len(x)
        return x, np.full((n, ), fill_value=-np.log(n))

class Sampler:
    def __init__(self, mean, cov, p):
        k, d = mean.shape
        k, d, d = cov.shape
        k = p.shape
        self.mean = mean
        self.cov = cov
        self.icov = np.concatenate([np.linalg.inv(cov)[None, :, :] for cov in self.cov], axis=0)
        det = np.array([np.linalg.det(cov) for cov in self.cov])
        self.norm = np.sqrt((2 * np.pi) ** d * det)
        self.p = p
        self.dim = d

    def __call__(self, n):
        k, d = self.mean.shape
        indices = np.random.choice(k, n, p=self.p)
        pos = np.zeros((n, d), dtype=np.float32)
        for i in range(k):
            mask = indices == i
            size = mask.sum()
            pos[mask] = np.random.multivariate_normal(self.mean[i], self.cov[i], size=size)
        return pos, np.full((n,), fill_value=-np.log(n))

    def log_prob(self, x):
        # b, d = x.shape
        diff = x[:, None, :] - self.mean[None, :]  # b, k, d
        return np.sum(self.p[None, :] * np.exp(-np.einsum('bkd,kde,bke->bk',
                                                          [diff, self.icov, diff]) / 2) / self.norm, axis=1)


def make_gmm_1d(n, m):
    x_sampler = Sampler(mean=np.array([[1.], [2], [3]]), cov=np.array([[[.1]], [[.1]], [[.1]]]),
                        p=np.ones(3) / 3)
    y_sampler = Sampler(mean=np.array([[0.], [3], [5]]), cov=np.array([[[.1]], [[.1]], [[.4]]]),
                        p=np.ones(3) / 3)

    x, loga = x_sampler(n)
    y, logb = y_sampler(m)
    return (x, loga), (y, logb)

def make_gmm(n, m, d, modes):
    means_x = np.random.rand(modes, d)
    means_y = np.random.rand(modes, d)
    cov = np.repeat(np.eye(d)[None, :, :], modes, axis=0) * 1e-1
    x_sampler = Sampler(mean=means_x, cov=cov,
                        p=np.full(modes, fill_value=1/modes))
    y_sampler = Sampler(mean=means_y, cov=cov,
                        p=np.full(modes, fill_value=1/modes))

    x, loga = x_sampler(n)
    y, logb = y_sampler(m)
    return (x, loga), (y, logb)


def make_random_5d(n, m):
    x = np.random.randn(n, 5)
    y = np.random.randn(m, 5) + 10
    loga = np.full((x.shape[0], ), fill_value=-np.log(x.shape[0]))
    logb = np.full((y.shape[0], ), fill_value=-np.log(y.shape[0]))
    return (x, loga), (y, logb)


def get_cloud_3d(data_dir=None):
    a, x = get_dragon(data_dir)
    b, y = create_sphere(int(1e4))
    loga = np.full((x.shape[0], ), fill_value=-np.log(x.shape[0]))
    logb = np.full((y.shape[0], ), fill_value=-np.log(y.shape[0]))
    return (x, loga), (y, logb)