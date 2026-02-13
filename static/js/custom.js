let autocomplete;

function initAutoComplete(){
    // Initialize LocationIQ autocomplete
    const addressInput = document.getElementById('id_address');
    if (!addressInput) return;
    
    autocomplete = new locationiq.Autocomplete(addressInput, {
        key: LOCATIONIQ_ACCESS_TOKEN,
        limit: 5,
        dedupe: 1,
        countrycodes: 'in', // India - change to your country code
    });

    // Listen for selection event
    autocomplete.on('select', function(e) {
        console.log('Selected place:', e);
        onPlaceChanged(e);
    });
}

function onPlaceChanged(placeData){
    if (!placeData || !placeData.lat || !placeData.lon) {
        document.getElementById('id_address').placeholder = "Start typing...";
        return;
    }

    // Set latitude and longitude
    const latitude = placeData.lat;
    const longitude = placeData.lon;
    
    $('#id_latitude').val(latitude);
    $('#id_longitude').val(longitude);
    $('#id_address').val(placeData.display_name);

    // Get detailed address information using reverse geocoding
    fetch(`https://us1.locationiq.com/v1/reverse.php?key=${LOCATIONIQ_ACCESS_TOKEN}&lat=${latitude}&lon=${longitude}&format=json`)
        .then(response => response.json())
        .then(data => {
            console.log('Reverse geocode data:', data);
            const address = data.address || {};
            
            // Extract address components
            const country = address.country || '';
            const state = address.state || address.region || '';
            const city = address.city || address.town || address.village || '';
            const postcode = address.postcode || '';
            
            // Update form fields
            $('#id_country').val(country);
            $('#id_state').val(state);
            $('#id_city').val(city);
            $('#id_pin_code').val(postcode);
        })
        .catch(error => {
            console.error('Reverse geocoding error:', error);
            // Try to extract from display_name if reverse geocoding fails
            extractAddressFromDisplayName(placeData.display_name);
        });
}

function extractAddressFromDisplayName(displayName) {
    // Fallback: try to extract basic info from display name
    // Display name format is usually: "address, city, state, postcode, country"
    const parts = displayName.split(',').map(p => p.trim());
    if (parts.length >= 2) {
        $('#id_country').val(parts[parts.length - 1] || '');
        if (parts.length >= 3) {
            $('#id_state').val(parts[parts.length - 2] || '');
        }
        if (parts.length >= 4) {
            $('#id_city').val(parts[parts.length - 3] || '');
        }
    }
}


$(document).ready(function(){
    // add to cart
    $('.add_to_cart').on('click', function(e){
        e.preventDefault();
        
        food_id = $(this).attr('data-id');
        url = $(this).attr('data-url');
        
       
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response){
                console.log(response)
                if(response.status == 'login_required'){
                    swal(response.message, '', 'info').then(function(){
                        window.location = '/login';
                    })
                }else if(response.status == 'Failed'){
                    swal(response.message, '', 'error')
                }else{
                    $('#cart_counter').html(response.cart_counter['cart_count']);
                    $('#qty-'+food_id).html(response.qty);

                    // subtotal, tax and grand total
                    applyCartAmounts(
                        response.cart_amount['subtotal'],
                        response.cart_amount['tax_dict'],
                        response.cart_amount['grand_total']
                    )
                }
            }
        })
    })


    // place the cart item quantity on load
    $('.item_qty').each(function(){
        var the_id = $(this).attr('id')
        var qty = $(this).attr('data-qty')
        $('#'+the_id).html(qty)
    })

    // decrease cart
    $('.decrease_cart').on('click', function(e){
        e.preventDefault();
        
        food_id = $(this).attr('data-id');
        url = $(this).attr('data-url');
        cart_id = $(this).attr('id');
        
        
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response){
                console.log(response)
                if(response.status == 'login_required'){
                    swal(response.message, '', 'info').then(function(){
                        window.location = '/login';
                    })
                }else if(response.status == 'Failed'){
                    swal(response.message, '', 'error')
                }else{
                    $('#cart_counter').html(response.cart_counter['cart_count']);
                    $('#qty-'+food_id).html(response.qty);

                    applyCartAmounts(
                        response.cart_amount['subtotal'],
                        response.cart_amount['tax_dict'],
                        response.cart_amount['grand_total']
                    )

                    if(window.location.pathname == '/cart/'){
                        removeCartItem(response.qty, cart_id);
                        checkEmptyCart();
                    }
                    
                } 
            }
        })
    })


    // DELETE CART ITEM
    $('.delete_cart').on('click', function(e){
        e.preventDefault();
        
        cart_id = $(this).attr('data-id');
        url = $(this).attr('data-url');
        
        
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response){
                console.log(response)
                if(response.status == 'Failed'){
                    swal(response.message, '', 'error')
                }else{
                    $('#cart_counter').html(response.cart_counter['cart_count']);
                    swal(response.status, response.message, "success")

                    applyCartAmounts(
                        response.cart_amount['subtotal'],
                        response.cart_amount['tax_dict'],
                        response.cart_amount['grand_total']
                    )

                    removeCartItem(0, cart_id);
                    checkEmptyCart();
                } 
            }
        })
    })


    // delete the cart element if the qty is 0
    function removeCartItem(cartItemQty, cart_id){
            if(cartItemQty <= 0){
                // remove the cart item element
                document.getElementById("cart-item-"+cart_id).remove()
            }
        
    }

    // Check if the cart is empty
    function checkEmptyCart(){
        var cart_counter = document.getElementById('cart_counter').innerHTML
        if(cart_counter == 0){
            document.getElementById("empty-cart").style.display = "block";
        }
    }


    // apply cart amounts
    function applyCartAmounts(subtotal, tax_dict, grand_total){
        if(window.location.pathname == '/cart/'){
            $('#subtotal').html(subtotal)
            $('#total').html(grand_total)

            console.log(tax_dict)
            for(key1 in tax_dict){
                console.log(tax_dict[key1])
                for(key2 in tax_dict[key1]){
                    // console.log(tax_dict[key1][key2])
                    $('#tax-'+key1).html(tax_dict[key1][key2])
                }
            }
        }
    }

    // ADD OPENING HOUR
    $('.add_hour').on('click', function(e){
        e.preventDefault();
        var day = document.getElementById('id_day').value
        var from_hour = document.getElementById('id_from_hour').value
        var to_hour = document.getElementById('id_to_hour').value
        var is_closed = document.getElementById('id_is_closed').checked
        var csrf_token = $('input[name=csrfmiddlewaretoken]').val()
        var url = document.getElementById('add_hour_url').value

        console.log(day, from_hour, to_hour, is_closed, csrf_token)

        if(is_closed){
            is_closed = 'True'
            condition = "day != ''"
        }else{
            is_closed = 'False'
            condition = "day != '' && from_hour != '' && to_hour != ''"
        }

        if(eval(condition)){
            $.ajax({
                type: 'POST',
                url: url,
                data: {
                    'day': day,
                    'from_hour': from_hour,
                    'to_hour': to_hour,
                    'is_closed': is_closed,
                    'csrfmiddlewaretoken': csrf_token,
                },
                success: function(response){
                    if(response.status == 'success'){
                        if(response.is_closed == 'Closed'){
                            html = '<tr id="hour-'+response.id+'"><td><b>'+response.day+'</b></td><td>Closed</td><td><a href="#" class="remove_hour" data-url="/vendor/opening-hours/remove/'+response.id+'/">Remove</a></td></tr>';
                        }else{
                            html = '<tr id="hour-'+response.id+'"><td><b>'+response.day+'</b></td><td>'+response.from_hour+' - '+response.to_hour+'</td><td><a href="#" class="remove_hour" data-url="/vendor/opening-hours/remove/'+response.id+'/">Remove</a></td></tr>';
                        }
                        
                        $(".opening_hours").append(html)
                        document.getElementById("opening_hours").reset();
                    }else{
                        swal(response.message, '', "error")
                    }
                }
            })
        }else{
            swal('Please fill all fields', '', 'info')
        }
    });

    // REMOVE OPENING HOUR
    $(document).on('click', '.remove_hour', function(e){
        e.preventDefault();
        url = $(this).attr('data-url');
        
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response){
                if(response.status == 'success'){
                    document.getElementById('hour-'+response.id).remove()
                }
            }
        })
    })

    // Initialize LocationIQ autocomplete if address field exists
    if (document.getElementById('id_address')) {
        if (typeof locationiq !== 'undefined') {
            initAutoComplete();
        } else {
            console.warn('LocationIQ library not loaded');
        }
    }

   // document ready close 
});