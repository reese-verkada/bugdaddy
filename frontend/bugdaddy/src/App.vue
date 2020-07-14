<template>
  <div id="app">
    <Header v-bind:is-logged-in="isLoggedIn" v-bind:is-auth="isAuth" v-bind:is-admin="isAdmin"/>
    <div class="container">
      <div class="row">
        <div class="col-sm-12">
          <h2>{{ $route.name }}</h2>
          <hr>
        </div>
      </div>
        <router-view v-bind:is-admin="isAdmin"/>
    </div>
  </div>
</template>

<script>
import Header from '@/components/Header.vue'
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      isLoggedIn:false,
      isAuth:false,
      isAdmin:false
    }
  },
  components: {
    Header
  },
  created() {
    this.check_auth()
  },
  updated() {
    this.check_auth()
  },
  methods: {
    check_auth() {
      axios.get(`${this.$apiURL}/api/check_auth`)
        .then(resp => {
          this.isAuth = true
          if (resp.data['isLoggedIn']) {
            this.isLoggedIn = true
          } else {
            this.isLoggedIn = false
          }
          if (resp.data.isAdmin) {
            this.isAdmin = true
          } else {
            this.isAdmin = false
            this.$router.push({name:"Table",query:this.$route.query})
          }
        }).catch(err => {
          if (err.response.status === 401) {
            this.isAuth = false
            //window.location.href = `${this.$apiURL}/saml/sso/?next=${this.$apiURL}/api/redirect?to=${window.location.href}`
            if (this.$route.name != "Login") {
              this.$router.push({name:"Login", query:{next:window.location.href}})
            }
          }
        })
    }
  }
}
</script>

<style>
  body {
    background-color: rgb(238, 238, 238);
  }
  body.modal-open {
    overflow: hidden;
  }
</style>
