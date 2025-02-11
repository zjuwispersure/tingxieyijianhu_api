wx.request({
  url: 'http://127.0.0.1:5000/child/get',
  method: 'GET',
  header: {
    'Authorization': `Bearer ${wx.getStorageSync('token')}`
  },
  success(res) {
    console.log('Response:', res.data)
  },
  fail(err) {
    console.error('Error:', err)
  }
}) 