import numpy as np

def positional_encoding(seq_len, d_model):
    """
    Compute positional encoding using numpy and einsum.
    
    Args:
        seq_len (int): Length of the sequence.
        d_model (int): Dimensionality of the model (must be even).
    
    Returns:
        np.ndarray: Positional encoding matrix of shape (seq_len, d_model).
    """
    if d_model % 2 != 0:
        raise ValueError("d_model must be even for positional encoding.")
    
    # Position indices: (seq_len, 1)
    positions = np.arange(seq_len)[:, np.newaxis]  # shape (seq_len, 1)
    
    # Dimension indices: (d_model,)
    # We compute the division term for each dimension:
    # For even indices i: 10000^(2*i/d_model)
    # For odd indices i: same as previous even index (since we use i//2)
    # We'll create a vector of shape (d_model,) where each element is
    # 1 / 10000^(2 * (i // 2) / d_model)
    i = np.arange(d_model)
    angle_rates = 1 / np.power(10000, (2 * (i // 2)) / d_model)  # shape (d_model,)
    
    # Use einsum to multiply positions (seq_len,1) with angle_rates (d_model,)
    # resulting in (seq_len, d_model)
    angle_rads = np.einsum('ij,k->ik', positions, angle_rates)
    
    # Apply sin to even indices, cos to odd indices
    angle_rads[:, 0::2] = np.sin(angle_rads[:, 0::2])  # dim 2i
    angle_rads[:, 1::2] = np.cos(angle_rads[:, 1::2])  # dim 2i+1
    
    return angle_rads

# Example usage:
if __name__ == "__main__":
    seq_len = 5
    d_model = 6
    pe = positional_encoding(seq_len, d_model)
    print("Positional encoding shape:", pe.shape)
    print("Positional encoding:\n", pe)