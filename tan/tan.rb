def diff(h)
  h2 = Hash.new(0)
  h.each do |key, v|
    m, n = key
    h2[[m-1,n+1]] += v*n
    h2[[m+1,n-1]] -= v*m 
  end
  h2
end

h = Hash.new

h[[-1,1]] = 1

5.times do
  h = diff(h)
  p h
end