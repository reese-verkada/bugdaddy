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
      <div class="col-lg-1"></div>
      <div class="col-sm-12 col-lg-10 level" v-bind:style="{'background-color':newdisplayp.color}">
        <span class="labelandinput">
          <label>Priority Label:</label>
          <input size="5" v-model="newdisplayp.display_p">
        </span>
        <span class="labelandinput">
          <label>Raw P value greater than:</label>
          <input size="5" v-model="newdisplayp.low">
        </span>
        <span class="labelandinput">
          <label>Emoji Status:</label>
          <input size="3" v-model="newdisplayp.emoji">
        </span>
        <span class="labelandinput">
          <label>Color:</label>
          <input v-model="newdisplayp.color" type="color">
        </span>
        <button v-on:click="addData()" class="primary">Add</button>
      </div>
    </div>

		<div v-for="(level,index) in levels" class="row"">
      <div class="col-lg-1"></div>
      <div class="col-sm-12 col-lg-10 level" v-bind:style="{'background-color':level.color}">
        <span class="labelandinput">
          <label>Priority Label:</label>
          <input size="5" v-model="level.display_p">
        </span>
        <span class="labelandinput">
          <label>Raw P value greater than:</label>
          <input size="5" v-model="level.low">
        </span>
        <span class="labelandinput">
          <label>Emoji Status:</label>
          <input size="3" v-model="level.emoji">
        </span>
        <span class="labelandinput">
          <label>Color:</label>
          <input v-model="level.color" type="color">
        </span>
        <button v-on:click="updateData()" class="primary">Update</button>
        <button v-on:click="deleteData(index)" class="secondary">Delete</button>
      </div>
	 </div>
	</div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Display P Formula',
  data () {
    return {
      errors:[],
      success:false,
      levels:[],
      newdisplayp:{
        'display_p':null,
        'low':null,
        'color':null,
        'emoji':null
      }
    }
  },
  created () {
  	this.getData()
  },
  methods: {
  	getData() {
  	 axios.get(`${this.$apiURL}/api/display_p_formula`)
      .then(resp => {
        this.levels = resp.data
      })
  	},
    deleteData(index) {
      this.levels.splice(index,1)
      this.updateData()
    },
    updateData() {
      this.success = false
      this.errors = []
      axios.post(`${this.$apiURL}/api/display_p_formula`,this.levels)
        .then(resp => {
          this.success = "Display P Formula updated"
          this.levels = resp.data
          this.newdisplayp = {
            'display_p':null,
            'low':null,
            'color':null,
            'emoji':null
          }
        })
        .catch(err => {
          this.errors.push(err.response.data.message)
        })
    },
    addData() {
      if (this.newdisplayp.display_p && this.newdisplayp.low) {
        this.levels.push(this.newdisplayp)
        this.success = false
        this.errors = []
        axios.post(`${this.$apiURL}/api/display_p_formula`,this.levels)
          .then(resp => {
            this.success = "Display P Formula updated"
            this.levels = resp.data
            this.newdisplayp = {
              'display_p':null,
              'low':null,
              'color':null,
              'emoji':null
            }
          })
          .catch(err => {
            this.errors.push(err.response.data.message)
            this.levels.pop()
          })
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
  .level {
    box-shadow: rgba(0, 0, 0, 0.043) 0px 3px;
    border-radius: 8px;
    background-color: white;
    padding: 15px;
    margin: 15px 0;
  }
  .labelandinput {
    white-space: nowrap;
  }
</style>
