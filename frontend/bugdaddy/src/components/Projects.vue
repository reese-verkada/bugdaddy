<template>
	<div class="container">
		<div class="row">
      <div class="card" v-bind:key="JIRAproject.id" v-for="JIRAproject in JIRAprojects">
        <div class="section">
          <h3>{{ JIRAproject.name }}</h3>
        </div>
        <div class="section">
          <button class="secondary" v-if="trackedIds[JIRAproject.id]" v-on:click="setConfirmDelete(JIRAproject)">Untrack</button>
          <button v-on:click="deleteData(JIRAproject)" v-if="confirmDelete[JIRAproject.id]" class="secondary">Confirm</button>
          <p v-if="confirmDelete[JIRAproject.id]">Untracking will delete all information saved about issues in this project (including priority)</p>
          <button class="primary" v-if="!trackedIds[JIRAproject.id]" v-on:click="postData(JIRAproject)">Track</button>
        </div>
      </div>
    </div>
    <hr v-if="$route.name=='Projects'">
    <div class="row">
      <div v-if="$route.name=='Projects'" class="card large">
        <div class="section">
          <h3>Track Issue Manually</h3>
          <p>There are times you may want to track specific issues without tracking an entire JIRA project. Enter the issue's key below and click Track to begin tracking that issue.</p>
        </div>
        <div class="section">
          <input v-model="trackIssueKey" type="text" size="25" placeholder="Issue Key (e.g. ENG-1234)">
          <button class="primary" v-on:click="trackIssue()">Track</button>
          <p>{{ message }}</p>
        </div>
      </div>
    </div>
	</div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Projects',
  data () {
    return {
    	projects:[],
      JIRAprojects:[],
      confirmDelete:{},
      addProject:{"project_id":null},
      trackedIds:{},
      trackIssueKey:null,
      message:null
    }
  },
  created () {
    this.getData()
  },
  methods: {
    getData() {
      this.trackedIds = {}
      axios.get(`${this.$apiURL}/api/jira_get/project`)
        .then(resp => {
          this.JIRAprojects = resp.data
        })
        .catch(err => {
          console.log(err)
        })

      axios.get(`${this.$apiURL}/api/jira_projects`)
      .then(resp => {
        this.projects = resp.data
        this.projects.forEach(project => {
          this.$set(this.trackedIds,project.project_id,true)
        })
        console.log(resp.data)
      })
    },
    postData (project) {
      axios.post(`${this.$apiURL}/api/jira_projects`,{"project_id":project.id})
        .then(resp => {
          this.getData()
          this.addProject.project_id = null
        })
    },
    deleteData (project) {
      this.confirmDelete = {}
      axios.delete(`${this.$apiURL}/api/jira_projects`,{data:{
        "project_id":project.id
      }})
        .then(resp => {
          this.getData()
        })
    },
    setConfirmDelete(project) {
      this.$set(this.confirmDelete,project.id,!this.confirmDelete[project.id])
    },
    trackIssue() {
      if (this.trackIssueKey) {
        this.message = null
        axios.post(`${this.$apiURL}/api/jira_issues`,[{"issue_key":this.trackIssueKey}])
          .then(resp => {
            this.message = "Tracked issue successfully"
            this.trackIssueKey = null
          })
          .catch(err => {
            this.message = err.response.data.message
          })
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
	
</style>
