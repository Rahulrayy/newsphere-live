import numpy as np

MIN_ANCHORS = 50


def procrustes_align(src_coords, src_keys, tgt_coords, tgt_keys):
    tgt_lookup = {k: i for i, k in enumerate(tgt_keys) if k}
    pairs = [
        (i, tgt_lookup[k])
        for i, k in enumerate(src_keys)
        if k and k in tgt_lookup
    ]

    if len(pairs) < MIN_ANCHORS:
        print(f"alignment: only {len(pairs)} anchors "
              f"(need {MIN_ANCHORS}), skipping")
        return src_coords

    src_rows = [p[0] for p in pairs]
    tgt_rows = [p[1] for p in pairs]
    A = src_coords[src_rows]
    B = tgt_coords[tgt_rows]

    a_mean = A.mean(axis=0)
    b_mean = B.mean(axis=0)
    A_c    = A - a_mean
    B_c    = B - b_mean

    H        = A_c.T @ B_c
    U, S, Vt = np.linalg.svd(H)
    R        = Vt.T @ U.T

    a_norm_sq = (A_c ** 2).sum()
    scale     = S.sum() / a_norm_sq if a_norm_sq > 0 else 1.0

    aligned = (src_coords - a_mean) @ R.T * scale + b_mean

    err_before = np.linalg.norm(A - B, axis=1).mean()
    A_fit      = (A - a_mean) @ R.T * scale + b_mean
    err_after  = np.linalg.norm(A_fit - B, axis=1).mean()
    print(f"alignment: {len(pairs)} anchors, "
          f"mean err {err_before:.3f} -> {err_after:.3f}, scale={scale:.3f}")

    return aligned