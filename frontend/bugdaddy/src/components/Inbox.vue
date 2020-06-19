<template>
  <div class="container">
    <button v-on:click="getData()" class="refresh">Refresh Inbox</button>
    <div class="row">
      <div class="col-md-2"></div>
      <div class="col-sm">
        <div v-if="!items" class="row inboxitem zero">
          <div class="col-sm">
            <h1>Inbox at zero; you're my superhero!</h1>
            <img src="/static/beach-vacation.svg">
          </div>
        </div>
        <div v-if="items" class="row inboxitem inboxheader">
          <div>
            <h1 v-if="items > 1"><span class="icon-mail"></span> {{ items }} tasks in your inbox</h1>
            <h1 v-if="items == 1"><span class="icon-mail"></span> 1 task in your inbox</h1>
            <p>The {{this.$appName}} inbox provides you with an overview of the tasks that require your attention.</p>
          </div>
        </div>
        <div v-show="jira_projects['data'] == 0" class="row inboxitem">
          <div class="col-sm">
            <h1>{{ jira_projects['title'] }}</h1>
            <p>{{ jira_projects['description'] }}</p>
            <Projects/>
          </div>
        </div>
        <div v-show="weighted_variables['data'] == 0" class="row inboxitem">
          <div class="col-sm">
            <h1>{{ weighted_variables['title'] }}</h1>
            <p>{{ weighted_variables['description'] }}</p>
            <WeightedVariables/>
          </div>
        </div>
        <div v-show="raw_p_formula['data'] == 0" class="row inboxitem">
          <div class="col-sm">
            <h1>{{ raw_p_formula['title'] }}</h1>
            <p>{{ raw_p_formula['description'] }}</p>
            <RawPFormula/>
          </div>
        </div>
        <div v-show="display_p_formula['data'] == 0" class="row inboxitem">
          <div class="col-sm">
            <h1>{{ display_p_formula['title'] }}</h1>
            <p>{{ display_p_formula['description'] }}</p>
            <DisplayPFormula/>
          </div>
        </div>
        <div v-show="weighted_variable_values['data']" class="row inboxitem">
          <div class="col-sm">
            <h1>{{ weighted_variable_values['title'] }}</h1>
            <p>{{ weighted_variable_values['description'] }}</p>
            <div v-for="issue in weighted_variable_values.data" class="card fluid editissuebutton">
              <input type="checkbox" v-bind:id="issue.issue_id" class="modal">
              <div>
                <div class="card editIssueModal">
                  <label v-on:click="getData()" v-bind:for="issue.issue_id" class="modal-close" ></label>
                  <h3 v-bind:style="{'background-color':issue.color}" class="section">{{ issue.issue_key }}</h3>
                  <EditIssue class="section" v-bind:issue="issue" v-if="currentIssue == issue.issue_id"/>
                </div>
              </div>
              <label class="editissuelabel" v-on:click="currentIssue = issue.issue_id" v-bind:for="issue.issue_id">
                <div class="row">
                  <div class="col-sm-2">
                    <h4>{{issue.issue_key}}</h4>
                  </div>
                  <div class="col-sm-10">
                    <p>{{issue.summary}}</p>
                  </div>
                </div>
              </label>
           </div>
          </div>
        </div>
      </div>
      <div class="col-md-2"></div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import Projects from '@/components/Projects.vue'
import WeightedVariables from '@/components/WeightedVariables.vue'
import RawPFormula from '@/components/RawPFormula.vue'
import DisplayPFormula from '@/components/DisplayPFormula.vue'
import EditIssue from '@/components/EditIssue.vue'

axios.defaults.withCredentials = true

export default {
  name: 'Inbox',
  components: {
    Projects,
    WeightedVariables,
    RawPFormula,
    DisplayPFormula,
    EditIssue,
  },
  data () {
    return {
     items:0,
     jira_projects:{},
     weighted_variables:{},
     raw_p_formula:{},
     display_p_formula:{},
     weighted_variable_values:{},
     currentIssue:null,
    }
  },
  created() {
    this.getData()
  },
  methods: {
    deleteitem(deleteme) {
      this.items = this.items.filter(item => item != deleteme);
    },
    getData() {
      this.currentIssue = null
      axios.get(`${this.$apiURL}/api/concierge`)
        .then(resp => {
          this.items = 0
          this.jira_projects = {}
          this.weighted_variables = {}
          this.raw_p_formula = {}
          this.display_p_formula = {}
          this.weighted_variable_values = {}
          if (resp.data['jira_projects']){
            this.jira_projects = resp.data['jira_projects']
            if (this.jira_projects['data'] == 0) {
              this.items++
            }
          }
          /*if (resp.data['weighted_variables']){
            this.weighted_variables = resp.data['weighted_variables']
            if (this.weighted_variables['data'] == 0) {
              this.items++
            }
          }*/
          /*if (resp.data['raw_p_formula']){
            this.raw_p_formula = resp.data['raw_p_formula']
            if (this.raw_p_formula['data'] == 0) {
              this.items++
            }
          }*/
          if (resp.data['display_p_formula']){
            this.display_p_formula = resp.data['display_p_formula']
            if (this.display_p_formula['data'] == 0) {
              this.items++
            }
          }
          /*if (resp.data['weighted_variable_values']){
            this.weighted_variable_values = resp.data['weighted_variable_values']
            if (this.weighted_variable_values['data']) {
              this.items += this.weighted_variable_values['data']
            }
          }*/
          if (this.items > 0){
            document.title = `(${this.items}) ${this.$appName}`
          } else {
            document.title = `${this.$appName}`
          }
      })
    },
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .inboxitem {
    box-shadow: rgba(0, 0, 0, 0.043) 0px 3px;
    border-radius: 8px;
    background-color: white;
    padding: 15px;
    margin: 30px 0;
  }
  .zero img{
    margin: 0 auto;
    display: block;
  }
  .zero {
    background: rgb(255,255,255);
    background: linear-gradient(0deg, rgba(255,255,255,1) 50%, rgba(74,208,254,1) 100%);
    color: white;
  }
  .refresh {
    position: fixed;
    bottom: 25px;
    right: 25px;
    z-index: 100;
  }
  .editissuebutton:hover {
    border-width: 1px;
    border-color: #0288d1;
    border-style: solid;
  }
  .editissuelabel:hover {
    cursor: pointer;
  }
  .editIssueModal {
    max-width:90%;
  }
</style>
