/**

Custom pagination plugin that calls a custom external function called
saveError() to let the user know of any error while saving an entry on Lotte
right before proceed with a page change.

The user can choose to continue to the desired page or stay and fix the error
that happened. For the first case, the content of the translation with error
will be lost.

**/

$.fn.dataTableExt.oPagination.iFullNumbersShowPages = 5;
$.fn.dataTableExt.oPagination.customFullNumbers =	{
			"fnInit": function ( oSettings, nPaging, fnCallbackDraw )
			{
			    nPaging.className = "dataTables_paginate paging_full_numbers";
				var nFirst = document.createElement( 'span' );
				var nPrevious = document.createElement( 'span' );
				var nList = document.createElement( 'span' );
				var nNext = document.createElement( 'span' );
				var nLast = document.createElement( 'span' );

				nFirst.innerHTML = oSettings.oLanguage.oPaginate.sFirst;
				nPrevious.innerHTML = oSettings.oLanguage.oPaginate.sPrevious;
				nNext.innerHTML = oSettings.oLanguage.oPaginate.sNext;
				nLast.innerHTML = oSettings.oLanguage.oPaginate.sLast;

				nFirst.className = "first paginate_button";
				nPrevious.className = "previous paginate_button";
				nNext.className= "next paginate_button";
				nLast.className = "last paginate_button";

				nPaging.appendChild( nFirst );
				nPaging.appendChild( nPrevious );
				nPaging.appendChild( nList );
				nPaging.appendChild( nNext );
				nPaging.appendChild( nLast );

				$(nFirst).click( function () {
						if (saveError()) {
							//fnCallbackDraw(oSettings);
						} else {
							if (oSettings.oApi._fnPageChange(oSettings, "first")) {
								aroundPagination(oSettings, fnCallbackDraw);
							}
						}
				} );

				$(nPrevious).click( function() {
						if (saveError()) {
							//fnCallbackDraw(oSettings);
						} else {
							if (oSettings.oApi._fnPageChange(oSettings, "previous")) {
								aroundPagination(oSettings, fnCallbackDraw);
							}
						}
				} );

				$(nNext).click( function() {
						if (saveError()) {
							//fnCallbackDraw(oSettings);
						} else {
							if (oSettings.oApi._fnPageChange(oSettings, "next")) {
								aroundPagination(oSettings, fnCallbackDraw);
							}
						}
				} );

				$(nLast).click( function() {
						if (saveError()) {
							//fnCallbackDraw(oSettings);
						} else {
							if (oSettings.oApi._fnPageChange(oSettings, "last")) {
								aroundPagination(oSettings, fnCallbackDraw);
							}
						}
				} );

				/* Take the brutal approach to cancelling text selection */
				$('span', nPaging)
					.bind( 'mousedown', function () { return false; } )
					.bind( 'selectstart', function () { return false; } );

				/* ID the first elements only */
				if ( oSettings.sTableId !== '' && typeof oSettings.aanFeatures.p == "undefined" )
				{
					nPaging.setAttribute( 'id', oSettings.sTableId+'_paginate' );
					nFirst.setAttribute( 'id', oSettings.sTableId+'_first' );
					nPrevious.setAttribute( 'id', oSettings.sTableId+'_previous' );
					nNext.setAttribute( 'id', oSettings.sTableId+'_next' );
					nLast.setAttribute( 'id', oSettings.sTableId+'_last' );
				}
			},

			"fnUpdate": function ( oSettings, fnCallbackDraw )
			{
				if ( !oSettings.aanFeatures.p )
				{
					return;
				}

				var iPageCount = 5;
				var iPageCountHalf = Math.floor(iPageCount / 2);
				var iPages = Math.ceil((oSettings.fnRecordsDisplay()) / oSettings._iDisplayLength);
				var iCurrentPage = Math.ceil(oSettings._iDisplayStart / oSettings._iDisplayLength) + 1;
				var sList = "";
				var iStartButton, iEndButton, i, iLen;
				//var oClasses = oSettings.oClasses;

				/* Pages calculation */
				if (iPages < iPageCount)
				{
					iStartButton = 1;
					iEndButton = iPages;
				}
				else
				{
					if (iCurrentPage <= iPageCountHalf)
					{
						iStartButton = 1;
						iEndButton = iPageCount;
					}
					else
					{
						if (iCurrentPage >= (iPages - iPageCountHalf))
						{
							iStartButton = iPages - iPageCount + 1;
							iEndButton = iPages;
						}
						else
						{
							iStartButton = iCurrentPage - Math.ceil(iPageCount / 2) + 1;
							iEndButton = iStartButton + iPageCount - 1;
						}
					}
				}

				/* Build the dynamic list */
				for ( i=iStartButton ; i<=iEndButton ; i++ )
				{
					if ( iCurrentPage != i )
					{
						sList += '<span class="paginate_button">'+i+'</span>';
					}
					else
					{
						sList += '<span class="paginate_active">'+i+'</span>';
					}
				}

				/* Loop over each instance of the pager */
				var an = oSettings.aanFeatures.p;
				var anButtons, anStatic, nPaginateList;

				var fnClick = function() {
					if (saveError()) {
						//fnCallbackDraw(oSettings, true);
						return false;
					}
					/* Use the information in the element to jump to the required page */
					var iTarget = (this.innerHTML * 1) - 1;
					oSettings._iDisplayStart = iTarget * oSettings._iDisplayLength;
					aroundPagination(oSettings, fnCallbackDraw);
					return false;
				};

				var fnFalse = function () { return false; };

				for ( i=0, iLen=an.length ; i<iLen ; i++ )
				{
					if ( an[i].childNodes.length === 0 )
					{
						continue;
					}

					/* Build up the dynamic list forst - html and listeners */
					var qjPaginateList = $('span:eq(2)', an[i]);
					qjPaginateList.html( sList );
					$('span', qjPaginateList).click( fnClick ).bind( 'mousedown', fnFalse )
						.bind( 'selectstart', fnFalse );

					/* Update the 'premanent botton's classes */
					anButtons = an[i].getElementsByTagName('span');
					anStatic = [
						anButtons[0], anButtons[1],
						anButtons[anButtons.length-2], anButtons[anButtons.length-1]
					];
					$(anStatic).removeClass( "paginate_button paginate_active paginate_button");
					if ( iCurrentPage == 1 )
					{
						anStatic[0].className += " paginate_button";
						anStatic[1].className += " paginate_button";
					}
					else
					{
						anStatic[0].className += " paginate_button";
						anStatic[1].className += " paginate_button";
					}

					if ( iPages === 0 || iCurrentPage == iPages || oSettings._iDisplayLength == -1 )
					{
						anStatic[2].className += " paginate_button";
						anStatic[3].className += " paginate_button";
					}
					else
					{
						anStatic[2].className += " paginate_button";
						anStatic[3].className += " paginate_button";
					}
				}
			}
		};
