<template>
	<div class="container">
		<div class="row">
      <span v-on:click="errors=[]" v-if="errors.length" class="toast error">
        <p v-for="error in errors">
          {{error}}
        </p>
      </span>
      <span v-on:click="success=false" v-if="success" class="toast success">
        <p>{{ success }}</p>
      </span>
      <div class="card large">
          <div class="section">
            <h3>Add Weighted Variable</h3>
          </div>
          <div class="section">
            <div class="row">
              <label for="newVariableName">Variable name: </label>
              <input id="newVariableName" v-model="new_variable.variable_name">
            </div>
            <div class="row">
              <label for="newVariableWeight">Variable weight: </label>
              <input id="newVariableWeight" size=3 v-model="new_variable.variable_weight">
            </div>
          </div>
          <div class="section">
            <button v-on:click="updateData(new_variable)" class="primary">Add</button>
          </div>
        </div>
	      <div class="card" v-bind:key="weighted_variable.variable_name" v-for="weighted_variable in weighted_variables">
	        <div class="section">
	          <h3>{{ weighted_variable.variable_name }}</h3>
	        </div>
          <div class="section">
            <label v-bind:for="weighted_variable.variable_name">Variable weight: </label>
            <input v-bind:id="weighted_variable.variable_name" size=3 v-model="weighted_variable.variable_weight">
          </div>
	        <div class="section">
            <button v-on:click="updateData(weighted_variable)" class="primary">Update</button>
	          <button v-on:click="deleteData(weighted_variable)" class="secondary">Delete</button>
	        </div>
	      </div>
	    </div>
	</div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'WeightedVariables',
  data () {
    return {
    	weighted_variables:[],
      errors:[],
      new_variable:{
        'variable_name':null,
        'variable_weight':1.0
      },
      success:false
    }
  },
  created () {
  	this.getData()
  },
  methods: {
  	getData() {
  		axios.get(`${this.$apiURL}/api/weighted_variables`)
      		.then(resp => {
        		this.weighted_variables = resp.data.weighted_variables
            this.errors = resp.data.errors
      	})
          .catch(err => {
            this.errors.push(err)
          })
  	},
    deleteData(variable) {
      axios.delete(`${this.$apiURL}/api/weighted_variables`,{data:[variable]})
        .then(resp => {
          this.weighted_variables = resp.data.weighted_variables
          this.errors = resp.data.errors
          this.success = false
        })
        .catch(err => {
            this.success = false
            this.errors.push(err)
        })
    },
    updateData(variable) {
      this.success = false
      axios.post(`${this.$apiURL}/api/weighted_variables`,[variable])
        .then(resp => {
          this.weighted_variables = resp.data.weighted_variables
          this.errors = resp.data.errors
          if (!this.errors.length) {
            this.new_variable = {
              'variable_name':null,
              'variable_weight':1.0
            }
            this.success = "Variable " + variable.variable_name + " updated successfully"
          }
        })
        .catch(err => {
          this.errors.push(err)
        })
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
