def IdTupleToLong(v):
  if len(v) != 8:
    raise ValueError, "Tuple must consist of 8 integers"
  ret = 0L
  for i in xrange(8):
    # this reverses the order of the tuple
    ret |= (v[i] << (i*8))
  return ret
