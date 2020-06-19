<template>
	<div class="container">
    <span v-on:click="errors=[]" v-if="errors.length" class="toast error">
        <p v-for="error in errors">
          {{error}}
        </p>
    </span>
    <span v-on:click="success=false" v-if="success" class="toast success">
      <p>{{ success }}</p>
    </span>

    <div class="row">
      <div class="card">
        <div class="section">
          <h3>Add Custom Attribute</h3>
          <input placeholder="Custom Attribute name" v-model="newAttribute">
        </div>
        <div class="section">
          <button v-on:click="addAttribute" class="primary">Add</button>
        </div>
      </div>

      <div class="card" v-for="(options, attr_name) in attributes">
        <div class="section">
          <h3>{{ attr_name }}</h3>
          <input v-for="(option, index) in options" v-model="attributes[attr_name][index]">
          <button v-on:click="addOption(attr_name)">+</button>
        </div>
        <div class="section">
          <button v-on:click="updateData" class="primary">Save</button>
          <button v-on:click="deleteAttribute(attr_name)" class="secondary">Delete</button>
        </div>
      </div>
    </div>

	</div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'CustomAttributes',
  data () {
    return {
      errors:[],
      success:false,
      attributes:{},
      newAttribute:""
    }
  },
  created () {
  	this.getData()
  },
  methods: {
  	getData() {
  	 axios.get(`${this.$apiURL}/api/custom_attributes`)
      .then(resp => {
        this.attributes = resp.data.attributes
      })
  	},
    updateData() {
      this.success = false
      this.errors = []
      axios.post(`${this.$apiURL}/api/custom_attributes`,this.attributes)
        .then(resp => {
          this.success = "Custom Attributes updated"
          this.attributes = resp.data.attributes
        })
        .catch(err => {
          this.errors.push(err.response.data.message)
        })
    },
    addOption(attribute) {
      if (this.attributes[attribute] && this.attributes[attribute].slice(-1)[0] != "") {
        this.attributes[attribute].push("")
      }
    },
    addAttribute() {
      if (this.newAttribute && !(this.newAttribute in this.attributes)) {
        this.$set(this.attributes,this.newAttribute,[])
        this.newAttribute = ""
      }
    },
    deleteAttribute(attribute) {
      if (attribute in this.attributes) {
        this.$delete(this.attributes,attribute)
        this.updateData()
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
	.error {
    background-color: #d32f2f;
  }
  .success {
    background-color: #bada55;
  }
</style>
