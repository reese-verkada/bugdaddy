<template>
	<div class="container">
		<div v-if="syncing" class="row">
			<span class="toast">Data is currently syncing...</span>
		</div>
		<div class="row">
			<div class="col-sm">
				<input size="35" id="filter" v-model="filterString" type="text" placeholder="Filter issues by string or regex...">
				<span class="tooltip bottom" aria-label="Filters all columns. Match any character or number. Use | for logical OR. Use ^ for matching start of string. Use $ for matching end of string."><span class="icon-help"></span></span>
        <button v-on:click="sync()" class="sync"><span v-bind:class="{'rainbow_text_animated':syncing}">Sync</span></button>
        <span v-if="syncErrors.length" class="card error">Sync failed</span>
        <span>{{sortedIssues.length}} {{sortedIssues.length == 1 ? "issue" : "issues"}} displayed</span>
			</div>
		</div>
		<div class="row">
			<div class="col-sm-12">
				<table class="hoverable sticky">
					<thead>
						<tr>
							<th v-for="col in columns" v-on:click="sort(col.id)">
								<span>{{ col.name }}</span>
								<span v-if="sortCol==col.id">{{ sortDirIcon }}</span>
							</th>
              <th v-for="(value, name) in custom_attributes">
                {{name}}<span v-on:click="toggleFilter(name)" v-bind:class="!isEmpty(attrFilters[name]) ? 'icon-filter-on' : 'icon-filter'"></span>
                <div class="attrFilter" v-show="currentlyOpenFilter == name">
                  <fieldset v-for="option in value">
                    <label v-bind:for="`${name}${option}`">{{option}}</label>
                    <input v-bind:checked="attrFilters[name][option]" v-on:change="updateFilter(name,option)" v-bind:id="`${name}${option}`" type="checkbox">
                  </fieldset>
                  <button v-on:click="toggleFilter(name)">Done</button>
                  <button v-on:click="attrFilters[name] = {}">Clear</button>
                </div>
              </th>
              
              <th>Emoji Status</th>
							<th v-if="isAdmin">Actions</th>
						</tr>
					</thead>
					<tr @keydown.esc="closeModal(issue.issue_id)" tabindex="0" v-on:dblclick="openModal(issue.issue_id)" v-bind:key="issue.issue_id" v-for="issue in sortedIssues" v-bind:style="{'background-color':issue.color}">
						<td data-label="Key">{{ issue.issue_key }}</td>
						<td data-label="Summary" v-bind:title="issue.summary">{{ issue.summary | truncate }}</td>
						<td data-label="Status">{{ issue.status }}</td>
						<td data-label="Priority">{{ issue.priority }}</td>
						<td data-label="Cases Attached">{{ issue.cases_attached }}</td>
						<td data-label="Total $">{{ issue.total_spend | currency}}</td>
            <td v-bind:data-label="custom_attribute" v-if="issue_attributes[issue.issue_id]" v-for="(options, custom_attribute) in custom_attributes">{{ issue_attributes[issue.issue_id][custom_attribute] }}</td>
            <td v-else></td>
            <td v-if="issue.emoji == '🔥'" data-label="Emoji Status"><img width=30px src="/static/fire.gif"></td>
            <td v-else data-label="Emoji Status"><span class="emoji">{{issue.emoji}}</span></td>
						<td v-if="isAdmin" data-label="Actions">
							<a target="_blank" v-bind:href="`${$apiURL}/api/jira_redirect/${issue.issue_key}`" title="Open issue in JIRA"><span class="icon-link"></span></a>
              <label v-on:click="openModal(issue.issue_id)"><span title="Edit issue" class="icon-edit"></span></label>
              <input type="checkbox" v-bind:id="issue.issue_id" class="modal">
              <div>
                <div v-on:dblclick.stop class="card editIssueModal">
                  <label v-on:click="openModal(issue.issue_id)" class="modal-close"></label>
                  <h3 v-bind:style="{'background-color':issue.color}" class="section">{{ issue.issue_key }} {{issue.emoji}}</h3>
                  <EditIssue v-on:saved="sync()" class="section" v-bind:issue="issue" v-bind:issue_attributes="issue_attributes[issue.issue_id]" v-bind:custom_attributes="custom_attributes" v-if="currentIssue == issue.issue_id"/>
                </div>
              </div>
              <span v-on:click="deleteIssue(issue.issue_id)" title="Untrack this issue" class="icon-trash"></span>
						</td>
					</tr>
				</table>
			</div>
		</div>
	</div>
</template>

<script>
import axios from 'axios'
import _ from 'lodash'
import EditIssue from '@/components/EditIssue.vue'

export default {
  name: 'Table',
  components: {
    EditIssue
  },
  data () {
    return {
    	issues:[],
      issue_attributes:{},
      custom_attributes:{},
      suggested_for_deletion:[],
    	syncing:true,
    	columns: [
    		{'id':'issue_key','name':'Key'},
    		{'id':'summary','name':'Summary'},
    		{'id':'status','name':'Status'},
        {'id':'priority','name':'Priority'},
    		//{'id':'display_p','name':'Priority'},
    		//{'id':'raw_p','name':'Raw P'},
    		{'id':'cases_attached','name':'Cases Attached'},
        {'id':'total_spend','name':'Total $'}
    	],
    	sortCol:'priority',
    	sortDir:'asc',
    	sortDirIcon:'▲',
    	filterString:'',
      attrFilters:{},
      syncErrors:[],
      currentIssue:null,
      currentlyOpenFilter:""
    }
  },
  created() {
  	this.getData()
  	this.sync()
  },
  props: {
    isAdmin: Boolean
  },
  methods:{
  	sync() {
      this.syncing = true
  		axios.get(`${this.$apiURL}/api/sync`)
  			.then(resp => {
  				this.syncing = false
          this.syncErrors = resp.data.errors
          this.suggested_for_deletion = []
          if (resp.data.suggested_for_deletion.issues) {
            resp.data.suggested_for_deletion.issues.forEach(i => {
              this.suggested_for_deletion.push(Number(i.id))
            })
          }
  				this.getData()
  			})
        .catch(err => {
          this.syncErrors.push(err)
          this.syncing = false
        })
  	},
  	getData() {
  		axios.get(`${this.$apiURL}/api/jira_issues`)
  			.then(resp => {
  				this.issues = resp.data
          
  			})
      axios.get(`${this.$apiURL}/api/custom_attributes`)
        .then(resp => {
          this.custom_attributes = resp.data.attributes
          for (const attr in this.custom_attributes) {
            this.$set(this.attrFilters, attr, {})
          }
        })
      axios.get(`${this.$apiURL}/api/issue_attributes`)
        .then(resp => {
          this.issue_attributes = resp.data
        })
  	},
  	sort(col) {
  		this.sortCol = col
  		this.sortDir = this.sortDir == 'desc' ? 'asc' : 'desc'
  		this.sortDirIcon = this.sortDirIcon == '▼' ? '▲' : '▼'
  	},
    deleteIssue(issue_id) {
      axios.delete(`${this.$apiURL}/api/jira_issues`,{data:[{"issue_id":issue_id}]})
        .then(resp => {
          this.sync()
        })
    },
    openModal(id,e) {
      this.currentIssue = id
      document.getElementById(id).click()
      document.body.classList.toggle("modal-open")
    },
    closeModal(id) {
      this.currentIssue = null
      document.body.classList.remove("modal-open")
      document.getElementById(id).checked = false
    },
    toggleFilter(name) {
      if (this.currentlyOpenFilter == name) {
        this.currentlyOpenFilter = ""
      }
      else {
        this.currentlyOpenFilter = name
      }
    },
    updateFilter (name, option) {
      if (this.attrFilters[name] && this.attrFilters[name][option]) {
        this.$delete(this.attrFilters[name], option)
      } else {
        this.$set(this.attrFilters[name],option,true)
      }
    },
    isEmpty(thing) {
      return _.isEmpty(thing)
    }
  },
  filters: {
  	truncate(text) {
  		if (text == null) {
        text = ''
      }
      return text.length <= 50 ? text : text.substring(0,50) + "..."
  	},
    currency(amount) {
      if (typeof amount !== "number") {
        return amount
      }
      return '$' + amount.toFixed(2).replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,')
    }
  },
  computed: {
    isAttrFilterOn() {
      for (const attr in this.attrFilters) {
        for (const option in this.attrFilters[attr]) {
          if (this.attrFilters[attr][option] === true) {
            return true
          }
        }
      }
      return false
    },
  	sortedIssues() {
  		return _.orderBy(this.issues,this.sortCol,this.sortDir)
  			.filter(issue => {
          if (this.isAttrFilterOn) { //If we're filtering by at least one attribute
            if (this.issue_attributes[issue.issue_id]) { //If the issue has at least one attribute set
              for (const attr in this.attrFilters) { //Go through every checked filter
                if (!_.isEmpty(this.attrFilters[attr])) {
                  if (this.issue_attributes[issue.issue_id][attr]) {  //Issue has this attr set and none of the options match
                    if (!(this.issue_attributes[issue.issue_id][attr] in this.attrFilters[attr])) {
                      return false
                    } else { //if an option does match, the option needs to = true
                      if (this.attrFilters[attr][this.issue_attributes[issue.issue_id][attr]] !== true) {
                        return false
                      }
                    }
                  } else { //Issue doesn't have attr set at all
                    return false
                  }
                }
              }
            } else { //If the issue doesn't have any attributes set, hide it (since it obvi won't match the filter)
              return false
            }
          }

  				for (const col in issue) {
  					if (RegExp(this.filterString.toLowerCase()).test(String(issue[col]).toLowerCase())) {
  						return true
  					}
  				}
  			})
  	}
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
	table {
		max-height: inherit;
		overflow: visible;
	}
	td, th {
		font-size: 75%;
		padding: 5px;
	}
  td {
    background-color: inherit;
  }
  span[class^=icon-] {
    font-size: 1rem;
  }
	.icon-edit {
    cursor: pointer;
  }
  .icon-trash {
    cursor: pointer;
    background-image: url('/static/trash.svg');
  }
  .icon-filter {
    cursor: pointer;
    background-image: url('/static/filter.svg');
  }
  .icon-filter-on {
    cursor: pointer;
    background-image: url('/static/filter-on.svg');
  }
	.editIssueModal {
    max-width:90%;
    max-height: 80vh !important;
    text-align: left;
  }
  span.card {
    display: inline;
  }
  .tooltip:after {
    white-space: normal;
    width: 300px;
  }
  .emoji {
    font-size: 1.5rem;
  }
  .rainbow_text_animated {
    background: linear-gradient(to right, #6666ff, #0099ff , #00ff00, #ff3399, #6666ff);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: rainbow_animation 1s ease-in-out infinite;
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
  button.sync:focus {
    outline: none;
  }
  .attrFilter {
    background-color: white;
    position: absolute;
    border-radius: 8px;
    box-shadow: rgba(0, 0, 0, 0.043) 0px 3px;
  }
  .attrFilter fieldset {
    border-radius: inherit;
  }
</style>
