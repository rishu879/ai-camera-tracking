"""Sensor noise and optical blur generation algorithms."""
import math
import random
import cv2
import numpy as np


def apply_gaussian_noise(image: np.ndarray, std_dev: float) -> np.ndarray:
    """
    Add zero-mean Gaussian thermal / readout noise with standard deviation sigma (up to 20 px).
    """
    if std_dev <= 0.0:
        return image

    noise = np.random.normal(0.0, std_dev, image.shape).astype(np.float32)
    noisy = image.astype(np.float32) + noise
    return np.clip(noisy, 0, 255).astype(np.uint8)


def apply_salt_and_pepper_noise(image: np.ndarray, ratio: float) -> np.ndarray:
    """
    Add Salt & Pepper impulse noise (ISRO spec: around 10% of image).
    """
    if ratio <= 0.0:
        return image

    r = min(0.15, max(0.0, ratio))
    output = image.copy()
    num_pixels = int(r * image.shape[0] * image.shape[1])

    # Salt (white pixels = 255)
    num_salt = num_pixels // 2
    y_coords = np.random.randint(0, image.shape[0], num_salt)
    x_coords = np.random.randint(0, image.shape[1], num_salt)
    output[y_coords, x_coords] = 255

    # Pepper (black pixels = 0)
    num_pepper = num_pixels - num_salt
    y_coords = np.random.randint(0, image.shape[0], num_pepper)
    x_coords = np.random.randint(0, image.shape[1], num_pepper)
    output[y_coords, x_coords] = 0

    return output


def apply_poisson_noise(image: np.ndarray) -> np.ndarray:
    """
    Simulate photon shot noise following Poisson distribution.
    """
    vals = len(np.unique(image))
    vals = 2 ** np.ceil(np.log2(max(vals, 2)))
    # Scaling to prevent saturation
    noisy = np.random.poisson(image.astype(np.float32))
    return np.clip(noisy, 0, 255).astype(np.uint8)


def apply_motion_blur(
    image: np.ndarray, kernel_size: int, angle_deg: float = 0.0
) -> np.ndarray:
    """
    Simulate linear motion blur via Point Spread Function (PSF) kernel convolution.
    """
    if kernel_size <= 1:
        return image

    k_size = int(kernel_size)
    if k_size % 2 == 0:
        k_size += 1

    # Create horizontal PSF kernel
    kernel = np.zeros((k_size, k_size), dtype=np.float32)
    kernel[k_size // 2, :] = 1.0

    # Rotate kernel by angle
    if abs(angle_deg) > 1e-3:
        M = cv2.getRotationMatrix2D((k_size / 2.0, k_size / 2.0), angle_deg, 1.0)
        kernel = cv2.warpAffine(kernel, M, (k_size, k_size))

    kernel /= np.sum(kernel) + 1e-7
    return cv2.filter2D(image, -1, kernel)


def apply_camera_blur(image: np.ndarray, sigma: float) -> np.ndarray:
    """
    Simulate optical defocus blur / Airy disc aberration using Gaussian kernel.
    """
    if sigma <= 0.0:
        return image

    k_size = int(round(sigma * 4)) | 1  # Ensure odd kernel size
    return cv2.GaussianBlur(image, (k_size, k_size), sigma)
