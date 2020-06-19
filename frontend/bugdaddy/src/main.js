// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'

var config = require('../static/config.json')

Vue.config.productionTip = false
Vue.prototype.$apiURL = config.API_URL
Vue.prototype.$appName = config.APP_NAME

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  components: { App },
  template: '<App/>'
})
