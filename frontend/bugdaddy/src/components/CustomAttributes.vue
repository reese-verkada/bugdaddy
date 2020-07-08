<template>
	<div class="container">
    <span v-on:click="errors=[]" v-if="errors.length" class="toast error">
        <p v-for="error in errors">
          {{ error }}
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
          <span v-for="(option, index) in options">
            <input v-model="attributes[attr_name][index]" v-on:blur="editAttributeOption(attr_name, index)">
            <span title="Delete this attribute option" class="icon-trash" v-on:click="deleteAttributeOption(attr_name, option)"></span>
          </span>
          <button v-on:click="addOption(attr_name)">+</button>
        </div>
        <div class="section">
          <button v-on:click="deleteAttribute(attr_name)" class="secondary">Delete</button>
        </div>
      </div>
    </div>

	</div>
</template>

<script>
import axios from 'axios'
import _ from 'lodash'

export default {
  name: 'CustomAttributes',
  data () {
    return {
      errors:[],
      success:false,
      attributes:{},
      serverAttributes:{},
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
        this.serverAttributes = _.cloneDeep(resp.data.attributes)
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
        this.success = false
        this.errors = []
        axios.delete(`${this.$apiURL}/api/custom_attributes/${attribute}`)
          .then(resp => {
            this.success = "Attribute " + attribute + " deleted"
            this.getData()
          })
          .catch(err => {
            this.errors.push(err.response.data.message)
          })
      }
    },
    deleteAttributeOption(attribute, option) {
      if (option != "") {
        if (attribute in this.attributes) {
          this.success = false
          this.errors = []
          axios.delete(`${this.$apiURL}/api/custom_attributes/${attribute}/${option}`)
            .then(resp => {
              this.success = "Attribute option " + option + " deleted"
              this.getData()
            })
            .catch(err => {
              this.errors.push(err.response.data.message)
            })
        }
      } else {
        this.attributes[attribute].pop()
      }
    },
    editAttributeOption(attribute, index) {
      if (this.serverAttributes[attribute] && this.serverAttributes[attribute][index]) { //if the attr option exists already
        if (this.attributes[attribute][index] != this.serverAttributes[attribute][index] && this.attributes[attribute][index] != "") { //Proceed if this is an edit
          this.success = false
          this.errors = []
          axios.post(`${this.$apiURL}/api/custom_attributes/${attribute}/${this.serverAttributes[attribute][index]}`,{'attr_option':this.attributes[attribute][index]})
            .then(resp => {
              this.success = "Attribute option " + this.serverAttributes[attribute][index] + " updated to " + this.attributes[attribute][index]
              this.getData()
            })
            .catch(err => {
              this.errors = err.response.data.errors
              this.getData()
            })
        }
      } else { //otherwise, we are adding a new option
        if (this.attributes[attribute][index] && this.attributes[attribute][index] != "") { //new option must exist
          this.success = false
          this.errors = []
          let payload = {}
          payload[attribute] = [this.attributes[attribute][index]]
          axios.post(`${this.$apiURL}/api/custom_attributes`,payload)
            .then(resp => {
              this.success = "Added attribute option " + this.attributes[attribute][index]
              this.getData()
            })
            .catch(err => {
              this.errors = err.response.data.errors
              this.getData()
            })
        }
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
  .icon-trash {
    cursor: pointer;
    background-image: url('/static/trash.svg');
  }
</style>
