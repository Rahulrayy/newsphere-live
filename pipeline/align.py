import numpy as np

MIN_ANCHORS = 50

# if the previous layout is squashed below this spread there's nothing
# meaningful to align to (and aligning would just copy the collapse forward)
MIN_TARGET_SPREAD = 1e-2


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

    tgt_spread = B_c.std(axis=0).min()
    if tgt_spread < MIN_TARGET_SPREAD:
        print(f"alignment: previous layout is degenerate "
              f"(spread {tgt_spread:.2e}), skipping")
        return src_coords

    H        = A_c.T @ B_c
    U, S, Vt = np.linalg.svd(H)

    # flip the last axis if svd hands back a reflection, we only want rotation
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1.0] * (H.shape[0] - 1) + [d])
    R = Vt.T @ D @ U.T

    # rotation + translation only. fitting a scale here shrinks the map a bit
    # every run (noisy anchors pull the least-squares scale below 1) and since
    # each run aligns to the last one it compounds until everything is one dot
    aligned = (src_coords - a_mean) @ R.T + b_mean

    err_before = np.linalg.norm(A - B, axis=1).mean()
    A_fit      = A_c @ R.T + b_mean
    err_after  = np.linalg.norm(A_fit - B, axis=1).mean()
    print(f"alignment: {len(pairs)} anchors, "
          f"mean err {err_before:.3f} -> {err_after:.3f}")

    return aligned
