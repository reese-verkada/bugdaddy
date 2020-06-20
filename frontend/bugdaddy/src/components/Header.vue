<template>
	<header class="row">
		<div class="col-sm">
		<span class="logo rainbow_text_animated">{{this.$appName}}</span>
		<span v-show="isAdmin">
			<router-link v-bind:class="{'highlighted':$route.name=='Inbox'}" class="button" to="/">Inbox</router-link>
		</span>
		<span v-show="isAuth">
			<router-link v-bind:class="{'highlighted':$route.name=='Table'}" class="button" to="/table">Table</router-link>
		</span>
		<span v-show="isAdmin">
			<router-link v-bind:class="{'highlighted':$route.name=='Projects'}" class="button" to="/projects">Projects</router-link>
			<router-link v-bind:class="{'highlighted':$route.name=='Weighted Variables'}" class="button" to="/weighted-variables">Weighted Variables</router-link>
			<router-link v-bind:class="{'highlighted':$route.name=='RawPFormula'}" class="button" to="/raw-p-formula">Priority Formula</router-link>
			<router-link v-bind:class="{'highlighted':$route.name=='DisplayPFormula'}" class="button" to="/display-p-formula">Display Settings</router-link>
			<router-link v-bind:class="{'highlighted':$route.name=='CustomAttributes'}" class="button" to="/custom-attributes">Custom Attributes</router-link>
		</span>
	</div>
	<div class="col-sm auth">
		<a v-bind:href="`${this.$apiURL}/saml/sso/?next=${this.$apiURL}/api/redirect?to=${pageURL}`"><span v-show="!isLoggedIn && $route.name!='Login'" class="button login">Log In</span></a>
		<a v-bind:href="`${this.$apiURL}/saml/logout/?next=${this.$apiURL}/api/redirect?to=${pageURL}`"><span v-show="isLoggedIn" class="button logout">Log Out</span></a>
	</div>
	</header>
</template>

<script>
export default {
  name: 'Header',
  data () {
    return {
    	pageURL: window.location.href
    }
  },
  updated() {
  	this.pageURL = window.location.href
  },
  props: {
  	isLoggedIn: Boolean,
  	isAuth: Boolean,
  	isAdmin: Boolean
  },
  methods: {
  	rainbowOn(event) {
  		event.target.className = "logo rainbow_text_animated"
  	},
  	rainbowOff(event) {
  		event.target.className = "logo"
  	}
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
	.highlighted {
		background-color: rgb(238, 238, 238);
	}

	.auth {
		text-align: right;
	}
	.login {
		color: #0288d1;
	}
	.logout {
		color: #d32f2f;
	}
	header.row {
		flex-wrap: nowrap;
	}
	.col-sm {
		max-width: none;
	}
	.rainbow_text_animated {
    background: linear-gradient(to right, #6666ff, #0099ff, #ff3399, #6666ff);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: rainbow_animation 60s ease-in-out infinite;
    background-size: 400% 100%;
	}	
	@keyframes rainbow_animation {
   		0%,100% {
        	background-position: 0 0;
    	}

    	50% {
        	background-position: 100% 0;
    	}
}

</style>
