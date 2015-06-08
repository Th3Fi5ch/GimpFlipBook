#!/usr/bin/env python

# GIMP Python plug-in to create flip books out of animated GIFs.
# Copyright Christoph Fischer 2015
#
#   <Image>/Image/Flip-book/(1) Prepare flip-book...
#   <Image>/Image/Flip-book/(2) Generate flip-book template...
#   <Image>/Image/Flip-book/(3) Generate flip-book printable images...
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gimpfu import *
import os

CONST_WIDTH = 900
CONST_HEIGHT = 400
CONST_GLUE_MARGIN = 300
CONST_CUT_MARGIN = 8

CONST_RESULT_COLS = 2
CONST_RESULT_ROWS = 3

CONST_PRINT_MARGIN = 1.02

CONST_RESULT_SUM = CONST_RESULT_ROWS * CONST_RESULT_COLS

CONST_BASE_WIDTH = CONST_WIDTH - CONST_GLUE_MARGIN - 2 * CONST_CUT_MARGIN
CONST_BASE_HEIGHT = CONST_HEIGHT - 2 * CONST_CUT_MARGIN


def plugin_prepare_flipbook( img, layer, approved ):
    if not approved:
        return

    pdb.gimp_image_undo_group_start( img )

    if img.base_type != RGB:
        pdb.gimp_convert_rgb( img )

    resize_to_base( img )
    pdb.gimp_image_undo_group_end( img )


def plugin_prepare_template( img, layer ):
    pdb.gimp_image_undo_group_start( img )

    # add glue marign in white
    gimp.set_foreground( 255, 255, 255 )
    gimp.set_background( 255, 255, 255 )
    pdb.gimp_context_set_brush_size( CONST_GLUE_MARGIN )

    img.resize( CONST_BASE_WIDTH + CONST_GLUE_MARGIN, CONST_BASE_HEIGHT, CONST_GLUE_MARGIN, 0 )
    for layer in img.layers:
        layer.resize( CONST_BASE_WIDTH + CONST_GLUE_MARGIN, CONST_BASE_HEIGHT, CONST_GLUE_MARGIN, 0 )
        pdb.gimp_pencil( layer, 4, [20, 0, 20, CONST_BASE_HEIGHT] )

    add_background_layer( img, 255, 255, 255 )

    # add cut marign in black
    img.resize( CONST_WIDTH, CONST_HEIGHT, CONST_CUT_MARGIN, CONST_CUT_MARGIN )
    resize_layers_to_image( img )

    add_background_layer( img, 0, 0, 0 )

    # add numbers on side in red
    add_numbers( img, 255, 0, 0 )

    pdb.gimp_image_undo_group_end( img )


def plugin_generate_pictures( original_image, layer, directory ):
    if not directory:
        pdb.gimp_message( 'Must choose a directory!' )
        return

    pdb.gimp_image_undo_group_start( original_image )

    gimp.set_background( 155, 155, 155 )
    # prepare base img
    oldlayers_length = len( original_image.layers )
    last_layer_copy = original_image.layers[oldlayers_length - 1].copy( )
    original_image.add_layer( last_layer_copy, oldlayers_length )

    img_num = 0
    image_new = layer_new = None
    for i in range( 0, oldlayers_length ):
        num_on_img = i % (CONST_RESULT_SUM)
        col_num = num_on_img % CONST_RESULT_COLS
        row_num = int( num_on_img / CONST_RESULT_COLS )

        if (num_on_img == 0):
            if (i != 0):
                add_final_cut_margin( image_new )
                save_final_image( image_new, directory, img_num, original_image.filename )
                img_num += 1
            # prepare image
            image_new = new_image( original_image )
            layer_new = new_layer( image_new )

        layers_length = len( original_image.layers )
        flatten_layer = pdb.gimp_image_merge_down( original_image, original_image.layers[layers_length - 2], CLIP_TO_BOTTOM_LAYER )
        pdb.gimp_edit_copy( flatten_layer )

        float_layer = pdb.gimp_edit_paste( layer_new, TRUE )
        pdb.gimp_floating_sel_to_layer( float_layer )
        float_layer.set_offsets( col_num * original_image.width, row_num * original_image.height )

    add_final_cut_margin( image_new )
    save_final_image( image_new, directory, img_num, original_image.filename )
    pdb.gimp_image_undo_group_end( original_image )

    pdb.gimp_message( 'Finished! You will find the flipbook images in ' + os.path.join( directory ) )


def save_final_image( img, dir, num, old_filename ):
    old_filename = os.path.splitext( os.path.basename( old_filename ) )[0]
    layer = pdb.gimp_image_merge_visible_layers( img, CLIP_TO_IMAGE )
    target_file = os.path.join( dir, old_filename + '-fbook' + str( num ) + '.jpg' )
    pdb.gimp_file_save( img, layer, target_file, '?' )
    #gimp.Display( img )


def add_final_cut_margin( img ):
    img.resize( int( CONST_PRINT_MARGIN * img.width ), int( CONST_PRINT_MARGIN * img.height ),
                int( (CONST_PRINT_MARGIN - 1) / 2 * img.width ), int( (CONST_PRINT_MARGIN - 1) / 2 * img.height ) )
    resize_layers_to_image( img )


def resize_to_base( img ):
    widthFactor = float( CONST_BASE_WIDTH ) / img.width
    heightFactor = float( CONST_BASE_HEIGHT ) / img.height

    if widthFactor > heightFactor:
        pdb.gimp_image_scale( img, int( widthFactor * img.width ), int( widthFactor * img.height ) )
    else:
        pdb.gimp_image_scale( img, int( heightFactor * img.width ), int( heightFactor * img.height ) )

    img.resize( CONST_BASE_WIDTH, CONST_BASE_HEIGHT, 0, 0 )
    resize_layers_to_image( img )


def resize_layers_to_image( img ):
    for layer in img.layers:
        x = layer.offsets[0]
        y = layer.offsets[1]
        layer.resize( img.width, img.height, x, y )


def add_background_layer( img, r, g, b ):
    layers_length = len( img.layers )
    last_layer_copy = img.layers[layers_length - 1].copy( )
    img.add_layer( last_layer_copy, layers_length )

    gimp.set_background( r, g, b )
    last_layer_copy.fill( BACKGROUND_FILL )

    pdb.gimp_image_merge_down( img, img.layers[layers_length - 1], CLIP_TO_BOTTOM_LAYER )


def add_numbers( img, r, g, b ):
    gimp.set_foreground( r, g, b )

    i = len( img.layers )
    for layer in img.layers:
        textlayer = pdb.gimp_text_fontname(
            img,
            layer,
            20,
            20,
            i,
            -1,     # border
            True,   # anitalias
            40,     # size
            0,      # sizeunit
            'Sans' )
        pdb.gimp_floating_sel_anchor( textlayer )
        i -= 1


def new_layer( img ):
    layer = pdb.gimp_layer_new( img, img.width, img.height, RGB_IMAGE, 'base', 100, NORMAL_MODE )
    layer.set_offsets( 0, 0 )
    pdb.gimp_image_add_layer( img, layer, 0 )
    return layer


def new_image( img ):
    new_img = pdb.gimp_image_new( CONST_RESULT_COLS * img.width, CONST_RESULT_ROWS * img.height, RGB )
    return new_img


register(
    "python_fu_flipbook_prepare",
    "Prepare a animated gif to create a flip-book.",
    "Prepare a animated gif to create a flip-book.",
    "Christoph Fischer",
    "Christoph Fischer",
    "2015",
    "<Image>/Image/Flip-book/(1) Prepare flip-book...",
    "*",
    [
        (PF_BOOL, 'approve', 'Your image should have a 3x2 ratio otherwise it will be automatically cropped: ', 0)
    ],
    [],
    plugin_prepare_flipbook )

register(
    "python_fu_flipbook_template",
    "Converts the prepared animated gif into a flipbook template",
    "Converts the prepared animated gif into a flipbook template",
    "Christoph Fischer",
    "Christoph Fischer",
    "2015",
    "<Image>/Image/Flip-book/(2) Generate flip-book template...",
    "RGB*, GRAY*",
    [],
    [],
    plugin_prepare_template )

register(
    "python_fu_flipbook_pictures",
    "Converts the prepared flipbook template into images for print",
    "Converts the prepared flipbook template into images for print",
    "Christoph Fischer",
    "Christoph Fischer",
    "2015",
    "<Image>/Image/Flip-book/(3) Generate flip-book printable images...",
    "RGB*, GRAY*",
    [
        (PF_DIRNAME, "directory", "Directory where the images will be saved: ", 0)
    ],
    [],
    plugin_generate_pictures )

main( )
