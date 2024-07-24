import os
import random
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F

from trainer import Trainer
from mnist import MNIST, get_dataloader


class MLPEncoder(nn.Module):
    def __init__(self, latent_dim=2):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Flatten(),
            nn.Linear(28*28, 256),
            nn.ReLU(),)
        self.mean = nn.Linear(256, latent_dim)
        self.log_var = nn.Linear(256, latent_dim)

    def forward(self, x):
        h = self.encoder(x)
        return self.mean(h), self.log_var(h)


class MLPDecoder(nn.Module):
    def __init__(self, latent_dim=2):
        super().__init__()
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 28*28),
            nn.Sigmoid(),
            nn.Unflatten(dim=1, unflattened_size=(1, 28, 28)),)

    def forward(self, z):
        x_pred = self.decoder(z)
        return x_pred

class CNNEncoder(nn.Module):
    def __init__(self, latent_dim=2):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 32, (3, 3), stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, (3, 3), stride=2, padding=1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(64*7*7, 256),
            nn.ReLU(),)
        self.mean = nn.Linear(256, latent_dim)
        self.log_var = nn.Linear(256, latent_dim)

    def forward(self, x):
        h = self.encoder(x)
        return self.mean(h), self.log_var(h)

class CNNDecoder(nn.Module):
    def __init__(self, latent_dim=2):
        super().__init__()
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 64*7*7),
            nn.ReLU(),
            nn.Unflatten(dim=1, unflattened_size=(64, 7, 7)),
            nn.ConvTranspose2d(64, 64, (4, 4), stride=2, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(64, 32, (4, 4), stride=2, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(32, 1, (3, 3), stride=1, padding=1),
            nn.Sigmoid(),)

    def forward(self, z):
        x_pred = self.decoder(z)
        return x_pred


class VAE(nn.Module):
    def __init__(self, encoder, decoder):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder

    def forward(self, x):
        mean, log_var = self.encoder(x)
        epsilon = torch.randn_like(mean)
        z = mean + torch.exp(0.5 * log_var) * epsilon
        x_pred = self.decoder(z)
        return x_pred, mean, log_var

def loss_vae(x_pred, x, mean, log_var):
    bce = nn.functional.binary_cross_entropy(x_pred, x, reduction='sum')
    kld = -0.5 * torch.sum(1 + log_var - mean.pow(2) - log_var.exp())
    return bce + kld

def binary_accuracy(x_pred, x_true):
    return torch.eq(x_pred.round(), x_true.round()).float().mean()


class TrainerVAE(Trainer):
    def train_step(self, x, y):
        x = x.to(self.device)
        self.optimizer.zero_grad()
        x_pred, mean, log_var = self.model(x)
        loss = self.loss_fn(x_pred, x, mean, log_var)
        loss.backward()
        self.optimizer.step()

        res = {"loss": loss.item()}
        for metric, metric_fn in self.metrics.items():
            if metric != "loss":
                res[metric] = metric_fn(x_pred, x).item()
        return res

    @torch.no_grad()
    def test_step(self, x, y):
        x = x.to(self.device)
        x_pred, mean, log_var = self.model(x)
        loss = self.loss_fn(x_pred, x, mean, log_var)

        res = {"loss": loss.item()}
        for metric, metric_fn in self.metrics.items():
            if metric != "loss":
                res[metric] = metric_fn(x_pred, x).item()
        return res


if __name__ == "__main__":

    manual_seed = 42
    random.seed(manual_seed)
    np.random.seed(manual_seed)
    
    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    model_type = "cnn"

    # data_dir = "/home/namu/myspace/NAMU_Tutorial/MNIST/Pytorch/MNIST/raw"
    # data_dir = "/home/namu/myspace/data/fashion_mnist"
    # data_dir = "/mnt/d/datasets/fashion_mnist_29M"
    data_dir = "/mnt/d/datasets/mnist_11M"
    
    mnist = MNIST(data_dir)
    train_images, train_labels = mnist.get_train_data()
    test_images, test_labels = mnist.get_test_data()
    
    train_loader = get_dataloader((train_images, train_labels), 
                                  batch_size=64, training=True,
                                  use_cuda=use_cuda)
    test_loader = get_dataloader((test_images, test_labels),
                                 batch_size=32, training=False, 
                                 use_cuda=use_cuda)

    print(device)
    print(train_images.shape, train_labels.shape)
    print(test_images.shape, test_labels.shape)
    
    x, y = next(iter(train_loader))
    print(x.shape, x.dtype, x.min().item(), x.max().item())
    print(y.shape, y.dtype, y.min().item(), y.max().item())

    if model_type == "cnn":
        print(">> Model Type: CNN")
        encoder = CNNEncoder()
        decoder = CNNDecoder()
    else:
        print(">> Model Type: MLP")
        encoder = MLPEncoder()
        decoder = MLPDecoder()
    
    model = VAE(encoder, decoder).to(device)
    
    loss_fn = loss_vae
    optimizer = torch.optim.Adam(model.parameters())
    metrics = {"acc": binary_accuracy}
    
    vae = TrainerVAE(model, optimizer, loss_fn, metrics=metrics)
    hist = vae.fit(train_loader, n_epochs=10, valid_loader=test_loader)
    
    res = vae.evaluate(test_loader)
    print(f">> Evaluation: loss={res['loss']:.3f}, acc={res['acc']:.3f}")
