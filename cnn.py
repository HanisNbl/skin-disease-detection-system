import tensorflow as tf

# Check if GPU is available
print("GPU available:", tf.config.list_physical_devices('GPU'))

# Perform simple computation on GPU
with tf.device('/GPU:0'):
    a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0])
    b = tf.constant([5.0, 4.0, 3.0, 2.0, 1.0])
    c = a + b

print("Result:", c)
