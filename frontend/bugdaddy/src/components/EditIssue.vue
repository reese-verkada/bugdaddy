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
    <h4>Issue Details:</h4>
    <div class="row">
      <div class="detail card fluid"><span class="bold">Summary:</span> {{ issue.summary }}</div>
      <div class="detail card fluid">
        <span class="bold">Priority:</span>
        <select v-on:change="updatePriority" v-model="newPriority" class="propertySelector">
          <option selected>{{ issue.priority }}</option>
          <option v-if="option.name != issue.priority" v-for="option in priorityOptions">{{ option.name }}</option>
        </select>
      </div>
      <div class="detail card fluid">
        <span class="bold">Status:</span>
        <select v-on:change="updateStatus" v-model="newStatus" class="propertySelector">
          <option selected>{{ issue.status }}</option>
          <option v-if="option.name != issue.status" v-bind:value="option" v-for="option in statusOptions">{{ option.name }}</option>
        </select>
        <select v-if="field.required" v-model="newStatus.fields[field.key].answer" class="propertySelector" v-for="field in newStatus.fields">
          <option v-bind:value="value" v-for="value in field.allowedValues">{{ value.name }}</option>
        </select>
        <button v-on:click="putStatus" v-if="newStatus != issue.status">Save</button>
      </div>
      <div class="detail card fluid" v-for="(options, custom_attribute) in custom_attributes">
        <span class="bold">{{ custom_attribute }}:</span>
        <select v-on:change="updateAttribute(issue.issue_id, custom_attribute, $event.target.value)" class="propertySelector">
          <option v-if="issue_attributes && issue_attributes[custom_attribute]">{{ issue_attributes[custom_attribute] }}</option>
          <option v-else selected disabled></option>
          <option v-if="!(issue_attributes && issue_attributes[custom_attribute] && issue_attributes[custom_attribute] == option)" v-for="option in options">{{ option }}</option>
        </select>
      </div>
    </div>
    <div class="row">
      <div class="detail card fluid"><span class="bold">Issue Key:</span> <a target="_blank" v-bind:href="`${$apiURL}/api/jira_redirect/${issue.issue_key}`">{{ issue.issue_key }}</a></div>
      <div v-if="issue[field.name]" v-for="field in fields" class="detail card fluid"><span class="bold">{{field.display}}:</span>
        <span v-if="field.filter">{{ format(issue[field.name],field.filter) }}</span>
        <span v-else>{{ issue[field.name] }}</span>
      </div>
    </div>
    
    <hr>
    <h4>Latest Notes:</h4>
    <div v-if="loadingComments" class="spinner primary"></div>
    <div class="comments" v-for="comment in comments">
      <img v-bind:src="comment.updateAuthor.avatarUrls['48x48']">
      <span class="displayName">{{comment.updateAuthor.displayName}}</span>
      <span class="updated">{{comment.updated | date}}</span>
      <p v-for="paragraph in comment.body.split('\n')">{{ paragraph }}</p>
    </div>
    <div class="comments">
      <div v-if="picker">
        <span class="button secondary suggestedUser" v-on:mousedown="replaceUser(user,$event)" v-bind:key="user.accountId" v-for="user in suggestedUsers">{{user.displayName}}</span>
      </div>
      <textarea placeholder="Add a note to this issue..." autofocus v-model="newCommentComputed"></textarea>
      <button class="primary" v-if="newCommentComputed" v-on:click="postComment()">Post</button>
    </div>
    <hr>
    <span v-for="variable in weighted_variables">
      <label>{{ variable.variable_name }}</label>
      <input v-model="weighted_variable_values[variable.variable_name]" size="5">
    </span>
    <button v-on:click="postData()" class="primary">Save</button>
  </div>
</template>

<script>
import axios from 'axios'
import moment from 'moment'
import _ from 'lodash'

export default {
  name: 'EditIssue',
  props: {
    issue: Object,
    issue_attributes: Object,
    custom_attributes: Object
  },
  created() {
    this.getData()
    this.newPriority = this.issue.priority
    this.newStatus = this.issue.status
  },
  data () {
    return {
      errors:[],
      success:false,
      weighted_variables:[],
      weighted_variable_values:{},
      priorityOptions:[],
      statusOptions:[],
      newPriority:"",
      newStatus:"",
      comments:[],
      newCommentDisplay:"",
      newCommentSend:"",
      accountIds:{},
      loadingComments:true,
      picker:"",
      suggestedUsers:[],
      fields: [
        {"name":"project_name","display":"Project"},
        {"name":"created_by","display":"First Linked To Issue"},
        {"name":"cases_attached","display":"Cases Attached"},
        {"name":"total_spend","display":"Total Spend","filter":"currency"}
      ]
    }
  },
  methods: {
    getData() {
      axios.get(`${this.$apiURL}/api/jira_get/priority`)
        .then(resp => {
          this.priorityOptions = resp.data
        })

      axios.get(`${this.$apiURL}/api/jira_get/issue/${this.issue.issue_id}/transitions?expand=transitions.fields`)
        .then(resp => {
          this.statusOptions = resp.data.transitions
        })

      this.loadingComments = true
      axios.get(`${this.$apiURL}/api/jira_comments/${this.issue.issue_key}`)
      .then(resp => {
        this.loadingComments = false
        this.comments = resp.data
      })
      axios.get(`${this.$apiURL}/api/weighted_variables`)
        .then(resp => {
          this.weighted_variables = resp.data.weighted_variables
        })
      axios.get(`${this.$apiURL}/api/weighted_variable_values?issue_id=${this.issue.issue_id}`)
        .then(resp => {
          let rawData = resp.data.weighted_variable_values
          rawData.forEach(e => {
            this.$set(this.weighted_variable_values,e.variable_name,e.value)
          })
        })
    },
    postData() {
      this.success = false
      this.errors = []
      let postPackage = []
      for (const variable_name in this.weighted_variable_values) {
        postPackage.push({
          'issue_id':this.issue.issue_id,
          'variable_name':variable_name,
          'value':this.weighted_variable_values[variable_name]
        })
      }
      axios.post(`${this.$apiURL}/api/weighted_variable_values?issue_id=${this.issue.issue_id}`,postPackage)
        .then(resp => {
          this.errors = resp.data.errors
          this.getData()
          if (!this.errors.length) {
            this.success = "Weighted variable values saved"
            this.$emit('saved',true)
          }
        })

    },
    postComment() {
      if (this.newCommentSend) {
        this.errors = []
        let payload = {"body":this.newCommentSend}
        axios.post(`${this.$apiURL}/api/jira_post/issue/${this.issue.issue_key}/comment`,payload)
          .then(resp => {
            this.newCommentComputed = ""
            this.getData()
          })
          .catch(err => {
            this.errors.push(err)
          })
      }
    },
    format(value, filter) {
      return this.$options.filters[filter](value)
    },
    replaceUser(user,event) {
      let tempComment = this.newCommentDisplay
      this.picker = ""
      this.newCommentDisplay = tempComment.replace(/^@[A-Za-z]+[ ]?[A-Za-z]*/,"<"+user.displayName+"> ")
      this.newCommentDisplay = this.newCommentDisplay.replace(/[ ]@[A-Za-z]+[ ]?[A-Za-z]*/," <" + user.displayName+"> ")
      this.accountIds["<"+user.displayName+">"] = user.accountId
      event.preventDefault()
    },
    updatePriority() {
      if (this.newPriority && this.newPriority != this.issue.priority) {
        this.success = false
        this.errors = []
        let payload = {
          "fields": {
            "priority": {
              "name": this.newPriority
            }
          }
        }
        axios.put(`${this.$apiURL}/api/jira_put/issue/${this.issue.issue_key}`,payload)
          .then(resp => {
            this.success = "Updated priority to " + this.newPriority
            this.$emit('saved',true)
            this.getData()
          })
          .catch(err => {
            this.success = false
            this.errors.push(err)
          })
      }
    },
    updateStatus() {
      if (this.newStatus && this.newStatus != this.issue.status) { //we're dealing with a transition here
        
        if (_.isEmpty(this.newStatus.fields) == false) { //if there are more fields required for the transition
          //set the default value for each field
          for (const field in this.newStatus.fields) {
            if (!("answer" in this.newStatus.fields[field]) && this.newStatus.fields[field].required) { //if default answer hasn't been set and an answer is required
              //pick the first one
              this.$set(this.newStatus.fields[field],"answer",this.newStatus.fields[field].allowedValues[0])
            }            
          }

        }
      }
    },
    putStatus() {
      this.success = false
      this.errors = []
      let payload = {
        "transition": {
          "id": this.newStatus.id
        },
        "fields" : {}
      }
      for (const field in this.newStatus.fields) { //for each field in the new status
        if (this.newStatus.fields[field].answer && this.newStatus.fields[field].answer.name) {
          payload.fields[field] = {"name":this.newStatus.fields[field].answer.name} //insert the answer into the payload object
        }
      }
      axios.post(`${this.$apiURL}/api/jira_post/issue/${this.issue.issue_id}/transitions`,payload)
        .then(resp => {
          this.success = "Updated status to " + this.newStatus.to.name
          this.$emit('saved',true)
          this.newStatus = this.newStatus.to.name
          this.getData()
        })
        .catch(err => {
          this.success = false
          this.errors.push(err)
        })
    },
    updateAttribute(issue_id, attr_name, attr_option) {
      if (issue_id && attr_name && attr_option) {
        this.success = false
        this.errors = []
        let payload = {
          "issue_id": issue_id,
          "attr_name": attr_name,
          "attr_option": attr_option
        }
        axios.post(`${this.$apiURL}/api/issue_attributes`,payload)
          .then(resp => {
            this.success = "Updated " + attr_name + " to " + attr_option
            this.$emit('saved',true)
            this.getData()
          })
          .catch(err => {
            this.success = false
            this.errors.push(err)
          })
      }
    }
  },
  filters: {
    currency(amount) {
      if (typeof amount !== "number") {
        return amount
      }
      return '$' + amount.toFixed(2).replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,')
    },
    date(date) {
      return moment(date).format("MMMM Do YYYY, h:mm:ss A") + " " + Intl.DateTimeFormat().resolvedOptions().timeZone
    },
    displayName(id) {
      return this.accountIds[id]
    }
  },
  computed: {
    newCommentComputed: {
      get() {
        if (this.picker) {
          axios.get(`${this.$apiURL}/api/jira_get/user/picker?maxResults=3&query=${this.picker}`)
            .then(resp => {
              this.suggestedUsers = resp.data.users
            })
        }
          this.newCommentSend = this.newCommentDisplay.replace(/<[a-zA-Z]+[ ]?[a-zA-Z]*>/gm,code => {
            return "[~accountid:"+this.accountIds[code]+"]"
          })
        return this.newCommentDisplay
      },
      set(typing) {
        this.newCommentDisplay = typing
        let picker = this.newCommentDisplay.match(/(^@|[ ]@)([A-Za-z]+[ ]?[A-Za-z]*)/)
        if (picker) {
          this.picker = picker[2]
        } else {
          this.picker = ""
        }
      }
    }
  }
}
</script>


<style scoped>
  .container {
    text-align: left !important;
    overflow: scroll;
  }
  .bold {
    font-weight: bold
  }
  .error {
    background-color: #d32f2f;
  }
  .success {
    background-color: #bada55;
  }
  .comments {
    box-shadow: rgba(0, 0, 0, 0.043) 0px 3px;
    border-radius: 8px;
    background-color: white;
    padding: 15px;
    margin: 10px 0;
  }
  .comments img {
    width: 48px;
    border-radius: 25px;
  }
  .comments .displayName {
    font-weight: bold;
  }
  .comments .updated {
    font-style: italic;
  }
  .detail {
    box-shadow: rgba(0, 0, 0, 0.043) 0px 3px;
    border-radius: 8px;
    background-color: white;
    padding: 15px;
    margin: 10px !important;
  }
  .comments textarea {
    display: block;
    resize: vertical;
    width: 100%;
  }
  .suggestedUser {
    border-radius: 30px;
  }
  .propertySelector {
    border: 0;
    outline: 0;
    background-color: inherit;
    padding: 0;
    margin: 0;
  }

</style>
