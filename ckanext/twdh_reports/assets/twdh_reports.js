"use strict";

ckan.module('twdh_reports', function ($) {
    return {
        options: {
            reportsParams: null
        },

        initialize: function () {
            console.log('twdh_reports module initialized');
            
            // Debug logs
            console.log('Params:', this.options.reportsParams);

            if (!this.options.reportsParams || !this.options.reportsParams.collection) {
                console.error('No collection data available');
                return;
            }

            try {
                const collection = JSON.parse(this.options.reportsParams.collection);
                console.log('Collection data:', collection);

                const datatable = $(this.el).DataTable({
                    data: collection,
                    pageLength: 10,
                    stateSave: true,
                    orderCellsTop: true,
                    autoWidth: true,
                    
                    // Column Definitions
                    columnDefs: [
                        {
                            targets: 0,
                            data: "name",
                            render: function(data) {
                                return data || 'Not Provided';
                            }
                        },
                        {
                            targets: 1,
                            data: "fullname",
                            render: function(data) {
                                return data || 'Not Provided';
                            }
                        },
                        {
                            targets: 2,
                            data: "title",
                            render: function(data) {
                  
                              return data.charAt(0).toUpperCase() + data.slice(1).toLowerCase();
                            }
                        },
                        {
                            targets: 3,
                            data: "email"
                        },
                        {
                            targets: 4,
                            data: "capacity",
                            render: function(data) {
                              if (!data) return 'Not Provided';
                              return data.charAt(0).toUpperCase() + data.slice(1).toLowerCase();
                            }
                        },
                        {
                            targets: 5,
                            data: "last_active",
                            render: function(data) {
                                if (!data) return 'Never';
                                return new Date(data).toLocaleString();
                            }
                        },
                        {
                            targets: 5,
                            data: "action",
                            orderable: false,
                            searchable: false,
                            render: function(data) {
                                return data || '<button class="btn btn-sm btn-outline-secondary">Action</button>';
                            }
                        }
                        
                    ],

                    
                    // DOM structure
                    dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
                         '<"row"<"col-sm-12 col-md-6"B>>' +
                         '<"row"<"col-sm-12"tr>>' +
                         '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',

                    // Button configuration
                    buttons: [
                        {
                            extend: 'csv',
                            text: '<i class="fa fa-file-text-o"></i> CSV',
                            className: 'btn btn-default',
                            exportOptions: {
                                columns: ':visible'
                            }
                        },
                        {
                            extend: 'excel',
                            text: '<i class="fa fa-file-excel-o"></i> Excel',
                            className: 'btn btn-default',
                            exportOptions: {
                                columns: ':visible'
                            }
                        },
                        {
                            extend: 'pdf',
                            text: '<i class="fa fa-file-pdf-o"></i> PDF',
                            className: 'btn btn-default',
                            exportOptions: {
                                columns: ':visible'
                            }
                        },
                        {
                            extend: 'print',
                            text: '<i class="fa fa-print"></i> Print',
                            className: 'btn btn-default',
                            exportOptions: {
                                columns: ':visible'
                            }
                        }
                    ],

                    // Initialize after table is ready
                    initComplete: function() {
                        const api = this.api();

                        // Add global search
                        const searchDiv = $('<div class="dataTables_filter"><label>Search: <input type="search" class="form-control form-control-sm" placeholder="Global search..."></label></div>')
                            .insertBefore($(api.table().container()).find('.dataTables_info'));

                        searchDiv.find('input').on('keyup change', function() {
                            api.search(this.value).draw();
                        });
                    }
                });

                // Store instance
                this.dataTable = datatable;

            } catch (error) {
                console.error('Error initializing DataTable:', error);
                console.error(error.stack);
            }
            
        },

        teardown: function() {
            if (this.dataTable) {
                this.dataTable.destroy();
            }
        }
    };
});