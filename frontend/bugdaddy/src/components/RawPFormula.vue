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
          <h3>Formula</h3>
          <input v-bind:class="{'selected':selected==index}" readonly v-on:focus="selected=index" v-bind:style="{width:splitFormula[index].length+4+'ch'}" v-for="(element,index) in splitFormula" v-model="splitFormula[index]">
          <div class="row">
            <button v-on:click="clearSelected()" class="secondary">Clear Selected Box</button>
            <button v-on:click="addBoxes()" class="inverse">Add Boxes</button>
            <button class="primary" v-on:click="updateData()">Update Formula</button>
          </div>
        </div>
        <div v-if="selected % 2 == 0" class="section">
          <h3>Operands</h3>
          <button v-on:click="pasteSelected(operand.variable_name)" v-for="operand in operands">{{ operand.variable_weight+' x '+operand.variable_name }}</button>
          <button v-on:click="pasteSelected('cases_attached')">cases_attached</button>
          <button v-on:click="pasteSelected(realNumber)">
            <label>Real Number:</label>
            <input v-model="realNumber" size="5" placeholder="0.5">
          </button>
        </div>
        <div v-if="selected % 2 == 1" class="section">
          <h3>Operators</h3>
             <button v-on:click="pasteSelected('+')">+</button>
             <button v-on:click="pasteSelected('*')">*</button>
        </div>
      </div>
    </div>
	</div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Raw P Formula',
  data () {
    return {
      formula: {'formula':null},
      splitFormula:[],
      operators:[],
      operands:[],
      errors:[],
      success:false,
      selected:0,
      realNumber:null
    }
  },
  created () {
  	this.getData()
  },
  methods: {
    getOperands() {
      axios.get(`${this.$apiURL}/api/weighted_variables`)
        .then(resp => {
          this.operands = resp.data.weighted_variables
        })
        .catch(err => {
          this.errors.push(err)
        })
    },
  	getData() {
      this.errors = []
      this.success = false
      axios.get(`${this.$apiURL}/api/raw_p_formula`)
        .then(resp => {
          this.formula = resp.data[0]
          if (this.formula) {
            this.splitFormula = this.formula.formula.split(" ")
      
          } else {
            this.splitFormula = ["","",""]
          }
          this.operands = this.getOperands()
        })
        .catch(err => {
          this.errors.push(err)
        })
  	},
    updateData() {
      this.errors = []
      this.success = false
      this.splitFormula = this.splitFormula.filter(e => e != "")
      this.formula = {'formula':this.splitFormula.join(" ")}
      axios.post(`${this.$apiURL}/api/raw_p_formula`,this.formula)
        .then(resp => {
          this.getData()
          this.success = "Raw P formula updated"
        })
        .catch(err => {
          this.errors.push(err.response.data.message)
        })
    },
    clearSelected() {
      this.$set(this.splitFormula,this.selected,"")
    },
    addBoxes() {
      let cond = this.splitFormula.filter(e => e == "")
      if (cond.length == 0) {
        this.splitFormula.push("")
        this.splitFormula.push("")
      }
    },
    pasteSelected(oper) {
      this.$set(this.splitFormula,this.selected,oper)
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
  .card {
    max-width: 100%;
  }
  .selected {
    border-width: 5px;
    border-color: #0288d1;
    border-style: solid;
    outline: none;
  }
  input:focus {
    outline:none;
    border-width: 5px;
    border-color: #0288d1;
    border-style: solid;
  }
</style>
