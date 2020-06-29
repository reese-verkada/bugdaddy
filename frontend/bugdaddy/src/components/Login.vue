<template>
	<div class="container">
		<div class="row">
      <div class="col-sm-0 col-md-2"></div>
      <div class="col-sm-12 col-md-8">
        <div class="card">
          <button v-on:click="go()">Log in with SSO</button>
        </div>
      </div>
      <div class="col-sm-0 col-md-2"></div>
    </div>
	</div>
</template>

<script>

export default {
  name: 'Login',
  data () {
    return {
    	
    }
  },
  methods: {
    go() {
      window.location.href = `${this.$apiURL}/saml/sso/?next=${this.$apiURL}/api/redirect?to=${this.$route.query.next}`
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
	.card {
    max-width: 100%;
  }
</style>
