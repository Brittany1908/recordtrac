// Manage the display of the record request table.
(function($) {

  Query = Backbone.Model.extend({

    defaults:
    {
      search_term: "",
      page_number: 1,
      // Using an attribute called 'page' makes weird things happen here. JFYI.
      per_page: 10,
      num_results: 0,
      is_closed: false,
      my_requests: true,
      department: ""
    },

    prev_page: function ()
    {
      this.set({ page_number: this.get("page_number") - 1 })
    },

    next_page: function ()
    {
      this.set({ page_number: this.get("page_number") + 1 })
      console.log( this.get("page_number") )
    }

  })

  Request = Backbone.Model.extend({})

  RequestSet = Backbone.Collection.extend({

    model: Request,

    initialize: function( models, options )
    {
      this._query = options.query
      this._query.on( "change", this.build, this )
    },

    url: function ()
    {
      return "/custom/request"
    },

    build: function ()
    {
      console.log("Fetching a new result set.")

      var data_params = {
        // "results_per_page": this._query.get("per_page"),
        "page": this._query.get("page_number"),
        "is_closed": this._query.get("is_closed"),
        "my_requests": this._query.get("my_requests")
      }

      var search_term = this._query.get("search_term")
      if ( search_term !== "" )
      {
        data_params["search"] = search_term
      }
      var department = this._query.get("department")
      if ( department != "")
      {
        data_params["department"] = department
      }

      this.fetch({
        data: data_params,
        dataType: "json",
        contentType: "application/json"
      });
    },

    parse: function ( response )
    {
      this._query.set({
        "num_results": response.num_results,
        "page": response.page
      })
      return response.objects
    }

  })

  // Smaller filter query control box that sits off to the side.
  FilterBox = Backbone.View.extend({

    initialize: function ()
    {
      this.model.on( "change", this.render, this )
    },

    render: function ()
    {
      var vars = {
        "is_closed": this.model.get( "is_closed" ),
        "my_requests": this.model.get( "my_requests"),
        "department": this.model.get( "department")
      }
      var template = _.template( $("#sidebar_template").html(), vars );
      this.$el.html( template );
    },

    events:
    {
      "click #is_closed": "toggle_show_closed",
      "click #my_requests": "toggle_my_requests",
      "change #department_name": "set_department"
    },

    toggle_show_closed: function ( event )
    {
      this.model.set( {
        "is_closed": !( this.model.get( "is_closed" ) )
      } )
    },
    toggle_my_requests: function ( event )
    {
      this.model.set( {
        "my_requests": !( this.model.get( "my_requests" ) )
      } )
    },
    set_department: function (event)
  {
    console.log(event.target.value)
    this.model.set("department", event.target.value)
  }    

  });


  SearchResults = Backbone.View.extend({

    initialize: function ()
    {
      this.collection.on( "sync", this.render, this )
    },

    render: function (event_name)
    {
      console.log("Rendering new results on event: " + event_name)
      var vars = { requests: this.collection.toJSON() }
      var template = _.template( $("#search_results_template").html(), vars )
      this.$el.html( template )
    },

    events:
    {
      "click .pagination .prev": "prev",
      "click .pagination .next": "next",
      "change #per-page": "update_per_page"
    },

    prev: function ()
    {
      this.model.prev_page()
    },

    next: function ()
    {
      this.model.next_page()
    },

    update_per_page: function ( event )
    {
      this.model.set("per_page", event.target.value)
    }

  });

  SearchField = Backbone.View.extend({

    initialize: function ()
    {
      this.render()
    },

    render: function ()
    {
      var template = _.template( 
        $("#search_field_template").html(), 
          { current_query: this.model.get("search_term") 
          }
        )

      this.$el.html( template )
    },

    events:
    {
      "keyup #search input": "set_search_term"
    },

    set_search_term: function ( event )
    {
      console.log( event.target.value )
      this.model.set( "search_term", event.target.value )
      this.model.set({ page_number: 1 })
    }

  });






  var query = new Query();
  var request_set = new RequestSet([], { query: query });
  var filter_box = new FilterBox({
    el: $("#sidebar_container"),
    model: query
  });
  var search_field = new SearchField({
    el: $("#search_field_container"),
    model: query
  });
  var search_results = new SearchResults({
    el: $("#search_results_container"),
    model: query,
    collection: request_set
  })

  query.set({ "page": 1 })

})(jQuery);
