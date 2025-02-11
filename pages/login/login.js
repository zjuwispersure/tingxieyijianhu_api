wx.login({
  success: res => {
    console.log('wx.login success:', res)
    if (res.code) {
      console.log('获取到的code:', res.code)
      wx.request({
        url: 'your_api_url/auth/login',
        method: 'POST',
        data: {
          code: res.code
        },
        success: function(res) {
          console.log('登录接口返回:', res)
        },
        fail: function(err) {
          console.error('登录请求失败:', err)
        }
      })
    }
  },
  fail: err => {
    console.error('wx.login fail:', err)
  }
}) 